"""Fetch a URL under the rules of the tool layer."""

import asyncio
import json
import logging
import time
from collections import Counter
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit

import httpx2
from pydantic import BaseModel

from src import robots
from src.config import USER_AGENT, Settings
from src.limits import RateLimiter, Sleep, TTLCache
from src.policy import PolicyError, check_url
from src.sanitise import sanitise_json, sanitise_text

log = logging.getLogger("tools")

MAX_REDIRECTS = 3
ROBOTS_TTL = 86_400.0
TEXT_TYPES = ("application/json", "application/xml", "application/rss+xml", "text/")


class UpstreamError(Exception):
    """The remote site could not give a usable answer."""


class TooLargeError(Exception):
    """The response is bigger than allowed."""


class FetchResult(BaseModel):
    url: str
    final_url: str
    status: int
    content_type: str
    body: str
    fetched_at: datetime
    cached: bool = False
    removed: int = 0


class Fetcher:
    def __init__(
        self,
        settings: Settings,
        client: httpx2.AsyncClient,
        limiter: RateLimiter | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self.settings = settings
        self.metrics: Counter[str] = Counter()
        self._client = client
        self._limiter = limiter or RateLimiter(settings.intervals, sleep=sleep)
        self._sleep = sleep
        self._cache: TTLCache[FetchResult] = TTLCache(settings.cache_ttl, settings.cache_entries)
        self._robots: TTLCache[list[robots.Rule]] = TTLCache(ROBOTS_TTL, 64)

    async def fetch(self, url: str) -> FetchResult:
        cached = self._cache.get(url)
        if cached is not None:
            self.metrics["cache_hits"] += 1
            return cached.model_copy(update={"cached": True})
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            # Every redirect target passes the same checks as the first URL
            host = check_url(current, self.settings.intervals)
            await self._check_robots(host, current)
            status, headers, content = await self._get(current, host)
            if status in (301, 302, 303, 307, 308) and "location" in headers:
                current = urljoin(current, headers["location"])
                continue
            result = self._build(url, current, status, headers, content)
            if status == 200:
                self._cache.put(url, result)
            return result
        raise UpstreamError("too many redirects")

    async def _check_robots(self, host: str, url: str) -> None:
        rules = self._robots.get(host)
        if rules is None:
            try:
                status, _, content = await self._get(f"https://{host}/robots.txt", host)
            except (UpstreamError, TooLargeError):
                # RFC 9309: when robots.txt is unreachable, assume everything is disallowed
                raise PolicyError(f"robots.txt of {host} is unreachable") from None
            if 200 <= status < 300:
                rules = robots.parse(content.decode("utf-8", "replace"), USER_AGENT)
            elif 400 <= status < 500:
                rules = robots.ALLOW_ALL
            else:
                rules = robots.DENY_ALL
            self._robots.put(host, rules)
        parts = urlsplit(url)
        path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        if not robots.is_allowed(rules, path):
            self.metrics["robots_blocked"] += 1
            raise PolicyError("disallowed by robots.txt")

    async def _get(self, url: str, host: str) -> tuple[int, httpx2.Headers, bytes]:
        headers = {"User-Agent": USER_AGENT}
        if host == "api.github.com" and self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        for attempt in range(1, self.settings.max_attempts + 1):
            await self._limiter.wait(host)
            self.metrics["requests"] += 1
            wait = float(2**attempt)
            try:
                async with self._client.stream("GET", url, headers=headers) as response:
                    limited = response.status_code == 429 or (
                        response.status_code == 403
                        and response.headers.get("x-ratelimit-remaining") == "0"
                    )
                    if not limited and response.status_code < 500:
                        content = await self._read(response)
                        return response.status_code, response.headers, content
                    wait = self._retry_wait(response.headers, wait)
                    problem = f"status {response.status_code}"
            except httpx2.TransportError as error:
                problem = type(error).__name__
            self.metrics["upstream_errors"] += 1
            log.warning("attempt %d for %s failed: %s", attempt, host, problem)
            if attempt == self.settings.max_attempts or wait > self.settings.max_wait:
                break
            await self._sleep(wait)
        raise UpstreamError(f"{host} failed: {problem}")

    async def _read(self, response: httpx2.Response) -> bytes:
        content = bytearray()
        async for chunk in response.aiter_bytes():
            content.extend(chunk)
            if len(content) > self.settings.max_bytes:
                raise TooLargeError("response is too large")
        return bytes(content)

    @staticmethod
    def _retry_wait(headers: httpx2.Headers, default: float) -> float:
        retry_after = headers.get("retry-after", "")
        if retry_after.isdigit():
            return float(retry_after)
        reset = headers.get("x-ratelimit-reset", "")
        if reset.isdigit():
            return max(float(reset) - time.time(), 1.0)
        return default

    def _build(
        self, url: str, final_url: str, status: int, headers: httpx2.Headers, content: bytes
    ) -> FetchResult:
        content_type = headers.get("content-type", "").split(";")[0].strip().lower()
        if content and not content_type.startswith(TEXT_TYPES):
            raise UpstreamError(f"unsupported content type: {content_type or '(none)'}")
        text = content.decode("utf-8", "replace")
        if content_type == "application/json":
            try:
                document, removed = sanitise_json(json.loads(text))
            except json.JSONDecodeError as error:
                raise UpstreamError("invalid JSON from upstream") from error
            body = json.dumps(document, ensure_ascii=False)
        else:
            body, removed = sanitise_text(text)
        self.metrics["blocked_injections"] += removed
        return FetchResult(
            url=url,
            final_url=final_url,
            status=status,
            content_type=content_type,
            body=body,
            fetched_at=datetime.now(UTC),
            removed=removed,
        )

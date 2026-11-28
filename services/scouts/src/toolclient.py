"""The only way a scout reaches the internet: through M5."""

import json
from typing import Any

import httpx2


class SourceError(Exception):
    """A page could not be fetched or understood."""


class ToolClient:
    def __init__(self, base_url: str, transport: httpx2.BaseTransport | None = None) -> None:
        # M5 may wait for a source's rate limit before answering
        self._client = httpx2.Client(base_url=base_url, timeout=180, transport=transport)

    def get_json(self, url: str) -> Any:
        try:
            response = self._client.post("/fetch", json={"url": url})
        except httpx2.TransportError as error:
            raise SourceError(f"tool layer unreachable: {type(error).__name__}") from error
        if response.status_code != 200:
            raise SourceError(f"tool layer refused ({response.status_code}): {response.text[:200]}")
        result = response.json()
        if result["status"] != 200:
            raise SourceError(f"source answered {result['status']}")
        try:
            return json.loads(result["body"])
        except json.JSONDecodeError as error:
            raise SourceError("source did not return JSON") from error

    def close(self) -> None:
        self._client.close()

"""Turn raw scout items into idea cards: normalise, deduplicate and chunk."""

import hashlib
import re
from collections import Counter
from collections.abc import Iterable
from datetime import date, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit

from pydantic import BaseModel

CHUNK_CHARS = 600
MIN_CONTENT = 20
MAX_TAGS = 10
# Tags that only name the source's own category say nothing about the idea
GENERIC_TAGS = {"showdev", "showhn", "opensource", "github"}
SENTENCE = re.compile(r"(?<=[.!?])\s+")
COMPLAINT = re.compile(
    r"\b(tired of|frustrat\w*|annoy\w*|wish\w*|struggl\w*|pain\w*|problem|hard to|difficult to|"
    r"no good|couldn'?t find|there (is|was) no)\b",
    re.IGNORECASE,
)


class RawItem(BaseModel):
    """The scouts' output (services/scouts/src/items.py)."""

    source: str
    external_id: str
    title: str
    summary: str = ""
    text: str = ""
    url: str
    published_at: date
    points: int = 0
    tags: list[str] = []
    fetched_at: datetime


class SourceRef(BaseModel):
    source: str
    url: str
    fetched_at: datetime


class Card(BaseModel):
    """Request body of the knowledge base `POST /cards`."""

    id: str
    name: str
    summary: str
    problem: str = ""
    customer: str = ""
    niche_tags: list[str] = []
    stage: str = "launched"
    funding_usd: int | None = None
    source: str
    url: str
    published_at: date
    fetched_at: datetime
    text: str = ""
    chunks: list[str]
    also_seen: list[SourceRef] = []


def canonical_url(url: str) -> str:
    """The same page written differently gives the same string."""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").removeprefix("www.")
    path = parts.path.rstrip("/")
    if host == "github.com":
        path = path.lower().removesuffix(".git")
    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parts.query)
            if not key.startswith("utm_") and key not in ("ref", "source")
        )
    )
    return f"{host}{path}" + (f"?{query}" if query else "")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _fingerprint(item: RawItem) -> str | None:
    """Same title and description on another address is the same idea."""
    words = re.findall(r"\w+", f"{item.title} {item.summary}".lower())
    return " ".join(words) if len(words) >= 6 else None


def split_chunks(text: str) -> list[str]:
    """Sentences grouped up to CHUNK_CHARS; the last sentence is repeated in the next chunk."""
    sentences: list[str] = []
    for sentence in SENTENCE.split(text.strip()):
        while len(sentence) > CHUNK_CHARS:
            cut = sentence.rfind(" ", 0, CHUNK_CHARS)
            cut = cut if cut > 0 else CHUNK_CHARS
            sentences.append(sentence[:cut])
            sentence = sentence[cut:].lstrip()
        if sentence:
            sentences.append(sentence)
    chunks: list[str] = []
    current: list[str] = []
    fresh = 0
    for sentence in sentences:
        if fresh and len(" ".join([*current, sentence])) > CHUNK_CHARS:
            chunks.append(" ".join(current))
            overlap = current[-1]
            keep = len(overlap) + len(sentence) < CHUNK_CHARS
            current, fresh = ([overlap] if keep else []), 0
        current.append(sentence)
        fresh += 1
    if fresh:
        chunks.append(" ".join(current))
    return chunks


def problem_sentence(text: str) -> str:
    """The first sentence that sounds like a complaint, else empty. A heuristic, not a summary."""
    for sentence in SENTENCE.split(text):
        if COMPLAINT.search(sentence):
            return sentence[:400]
    return ""


def _tags(items: list[RawItem]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        for tag in item.tags:
            tag = tag.strip().lower()
            if tag and tag not in GENERIC_TAGS:
                seen[tag] = None
    return list(seen)[:MAX_TAGS]


def _card(key: str, group: list[RawItem]) -> Card:
    # The earliest sighting names the card; the longest text describes it
    group.sort(key=lambda item: (item.published_at, item.source, item.external_id))
    first = group[0]
    text = max((item.text for item in group), key=len)
    summary = first.summary or first.title
    chunks = [f"{first.title}. {summary}" if summary != first.title else first.title]
    if text and text != summary and text != first.title:
        chunks += split_chunks(text)
    others: dict[tuple[str, str], SourceRef] = {}
    for item in group[1:]:
        if (item.source, item.url) != (first.source, first.url):
            others[(item.source, item.url)] = SourceRef(
                source=item.source, url=item.url, fetched_at=item.fetched_at
            )
    return Card(
        id=f"card_{_digest(key)}",
        name=first.title[:300],
        summary=summary[:2000],
        problem=problem_sentence(text),
        niche_tags=_tags(group),
        source=first.source,
        url=first.url,
        published_at=first.published_at,
        fetched_at=max(item.fetched_at for item in group),
        text=text,
        chunks=chunks[:50],
        also_seen=sorted(others.values(), key=lambda ref: (ref.source, ref.url)),
    )


def build_cards(items: Iterable[RawItem]) -> tuple[list[Card], Counter[str]]:
    """Return the cards and, per source, how many items were dropped or merged away."""
    dropped: Counter[str] = Counter()
    latest: dict[tuple[str, str], RawItem] = {}
    for item in items:
        # A later snapshot of the same item replaces the earlier one without counting as a drop
        identity = (item.source, item.external_id)
        if identity not in latest or item.fetched_at >= latest[identity].fetched_at:
            latest[identity] = item

    groups: dict[str, list[RawItem]] = {}
    fingerprints: dict[str, str] = {}
    for item in sorted(latest.values(), key=lambda i: (i.published_at, i.source, i.external_id)):
        if len(f"{item.title} {item.summary} {item.text}".strip()) < MIN_CONTENT:
            dropped[item.source] += 1
            continue
        key = canonical_url(item.url)
        fingerprint = _fingerprint(item)
        if key not in groups and fingerprint in fingerprints:
            key = fingerprints[fingerprint]
        if key in groups:
            dropped[item.source] += 1
        groups.setdefault(key, []).append(item)
        if fingerprint:
            fingerprints.setdefault(fingerprint, key)
    return [_card(key, group) for key, group in groups.items()], dropped

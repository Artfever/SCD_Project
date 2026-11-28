"""Request and response shapes (Guide section 2). To be aligned with contracts/ (issue #4)."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class Card(BaseModel):
    id: str = Field(pattern=r"^card_[A-Za-z0-9_-]{1,64}$")
    name: str = Field(min_length=1, max_length=300)
    summary: str = Field(max_length=2000)
    problem: str = ""
    customer: str = ""
    niche_tags: list[str] = Field(default=[], max_length=30)
    stage: str = "unknown"
    funding_usd: int | None = Field(default=None, ge=0)
    source: str = Field(min_length=1, max_length=40)
    url: str = Field(pattern=r"^https?://", max_length=2000)
    published_at: date | None = None
    fetched_at: datetime
    text: str = Field(default="", max_length=20_000)


class SourceRef(BaseModel):
    source: str = Field(min_length=1, max_length=40)
    url: str = Field(pattern=r"^https?://", max_length=2000)
    fetched_at: datetime


class CardWithChunks(Card):
    chunks: list[str] = Field(min_length=1, max_length=50)
    also_seen: list[SourceRef] = Field(default=[], max_length=50)


class CardBatch(BaseModel):
    cards: list[CardWithChunks] = Field(min_length=1, max_length=200)


class UpsertResult(BaseModel):
    added: int = 0
    updated: int = 0
    unchanged: int = 0


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    k: int = Field(default=10, ge=1, le=50)
    sources: list[str] | None = None
    niche: str | None = None
    published_after: date | None = None
    published_before: date | None = None


class Evidence(BaseModel):
    evidence_id: str
    card_id: str
    name: str
    quote: str
    source: str
    url: str
    published_at: date | None
    retrieved_at: datetime
    score: float


class SearchResponse(BaseModel):
    results: list[Evidence]


class IngestionRun(UpsertResult):
    run_id: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1, max_length=40)
    dropped: int = 0


class SourceStats(BaseModel):
    source: str
    cards: int
    newest_published: date | None
    last_fetched: datetime | None


class Stats(BaseModel):
    cards: int
    chunks: int
    sources: list[SourceStats]

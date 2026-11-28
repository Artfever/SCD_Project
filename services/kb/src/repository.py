"""All SQL of the knowledge base."""

import hashlib
from datetime import UTC, datetime
from typing import Any

from src.database import Database
from src.models import (
    Card,
    CardWithChunks,
    Evidence,
    IngestionRun,
    SearchRequest,
    SourceStats,
    Stats,
    UpsertResult,
)

CARD_COLUMNS = list(Card.model_fields)

UPSERT_CARD = f"""
INSERT INTO cards ({", ".join(CARD_COLUMNS)}, content_hash)
VALUES ({", ".join(f"%({column})s" for column in CARD_COLUMNS)}, %(content_hash)s)
ON CONFLICT (id) DO UPDATE SET
    {", ".join(f"{column} = EXCLUDED.{column}" for column in CARD_COLUMNS if column != "id")},
    content_hash = EXCLUDED.content_hash,
    updated_at = now()
"""

FILTERS = """
    (%(sources)s::text[] IS NULL OR c.source = ANY(%(sources)s))
AND (%(niche)s::text IS NULL OR %(niche)s = ANY(c.niche_tags))
AND (%(after)s::date IS NULL OR c.published_at >= %(after)s)
AND (%(before)s::date IS NULL OR c.published_at <= %(before)s)
"""

# Any query word may match (plainto_tsquery would require all of them); best chunk per card
KEYWORD_SEARCH = f"""
WITH q AS (
    SELECT replace(plainto_tsquery('english', %(query)s)::text, '&', '|')::tsquery AS terms
), matches AS (
    SELECT DISTINCT ON (k.card_id)
           k.chunk_id, k.card_id, k.text, ts_rank_cd(k.tsv, q.terms, 32) AS score
    FROM chunks k JOIN cards c ON c.id = k.card_id, q
    WHERE k.tsv @@ q.terms AND {FILTERS}
    ORDER BY k.card_id, score DESC, k.position
)
SELECT m.*, c.name, c.source, c.url, c.published_at
FROM matches m JOIN cards c ON c.id = m.card_id
ORDER BY m.score DESC, m.card_id
LIMIT %(limit)s
"""


def content_hash(card: CardWithChunks) -> str:
    # fetched_at changes on every run and must not count as a change
    return hashlib.sha256(card.model_dump_json(exclude={"fetched_at"}).encode()).hexdigest()


def search_parameters(request: SearchRequest, limit: int) -> dict[str, Any]:
    return {
        "query": request.query,
        "sources": request.sources,
        "niche": request.niche,
        "after": request.published_after,
        "before": request.published_before,
        "limit": limit,
    }


def evidence(row: dict[str, Any], retrieved_at: datetime) -> Evidence:
    return Evidence(
        evidence_id=row["chunk_id"],
        card_id=row["card_id"],
        name=row["name"],
        quote=row["text"],
        source=row["source"],
        url=row["url"],
        published_at=row["published_at"],
        retrieved_at=retrieved_at,
        score=float(row["score"]),
    )


class Repository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def ping(self) -> None:
        with self.database.connect() as connection:
            connection.execute("SELECT 1")

    def upsert(self, cards: list[CardWithChunks]) -> UpsertResult:
        result = UpsertResult()
        with self.database.connect() as connection:
            for card in cards:
                digest = content_hash(card)
                old = connection.execute(
                    "SELECT content_hash FROM cards WHERE id = %s", (card.id,)
                ).fetchone()
                if old and old["content_hash"] == digest:
                    result.unchanged += 1
                    connection.execute(
                        "UPDATE cards SET fetched_at = %s WHERE id = %s",
                        (card.fetched_at, card.id),
                    )
                else:
                    result.added += old is None
                    result.updated += old is not None
                    values = card.model_dump(exclude={"chunks"}) | {"content_hash": digest}
                    connection.execute(UPSERT_CARD.encode(), values)
                    connection.execute("DELETE FROM chunks WHERE card_id = %s", (card.id,))
                    for position, text in enumerate(card.chunks):
                        connection.execute(
                            "INSERT INTO chunks (chunk_id, card_id, position, text) "
                            "VALUES (%s, %s, %s, %s)",
                            (f"{card.id}#c{position}", card.id, position, text),
                        )
                connection.execute(
                    "INSERT INTO card_sources (card_id, platform, url, fetched_at) "
                    "VALUES (%s, %s, %s, %s) ON CONFLICT (card_id, platform, url) "
                    "DO UPDATE SET fetched_at = EXCLUDED.fetched_at",
                    (card.id, card.source, card.url, card.fetched_at),
                )
        return result

    def get(self, card_id: str) -> Card | None:
        query = f"SELECT {', '.join(CARD_COLUMNS)} FROM cards WHERE id = %s"
        with self.database.connect() as connection:
            row = connection.execute(query.encode(), (card_id,)).fetchone()
        return Card.model_validate(row) if row else None

    def search(self, request: SearchRequest) -> list[Evidence]:
        with self.database.connect() as connection:
            rows = connection.execute(
                KEYWORD_SEARCH.encode(), search_parameters(request, request.k)
            ).fetchall()
        now = datetime.now(UTC)
        return [evidence(row, now) for row in rows]

    def record_run(self, run: IngestionRun) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO ingestion_runs "
                "(run_id, source, added, updated, unchanged, dropped) VALUES "
                "(%(run_id)s, %(source)s, %(added)s, %(updated)s, %(unchanged)s, %(dropped)s) "
                "ON CONFLICT (run_id, source) DO NOTHING",
                run.model_dump(),
            )

    def stats(self) -> Stats:
        with self.database.connect() as connection:
            sources = connection.execute(
                "SELECT source, count(*) AS cards, max(published_at) AS newest_published, "
                "max(fetched_at) AS last_fetched FROM cards GROUP BY source ORDER BY source"
            ).fetchall()
            chunks = connection.execute("SELECT count(*) AS n FROM chunks").fetchone()
        rows = [SourceStats.model_validate(row) for row in sources]
        return Stats(
            cards=sum(row.cards for row in rows),
            chunks=chunks["n"] if chunks else 0,
            sources=rows,
        )

"""M6 Knowledge Base: searchable memory of idea cards and the source of every evidence id."""

import logging

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.database import Database
from src.models import (
    Card,
    CardBatch,
    IngestionRun,
    SearchRequest,
    SearchResponse,
    Stats,
    UpsertResult,
)
from src.repository import Repository

SERVICE = "kb"
log = logging.getLogger(SERVICE)


def create_app(repository: Repository | None = None) -> FastAPI:
    app = FastAPI(title=f"scd-{SERVICE}")
    store = repository or Repository(Database())

    @app.exception_handler(psycopg.OperationalError)
    def database_down(_: Request, error: psycopg.OperationalError) -> JSONResponse:
        log.error("database unavailable: %s", error)
        return JSONResponse({"detail": "database unavailable"}, status_code=503)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness: the process is running."""
        return {"status": "ok", "service": SERVICE}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        """Readiness: the database answers and is migrated (503 otherwise)."""
        store.ping()
        return {"status": "ready", "service": SERVICE}

    @app.post("/cards")
    def upsert(batch: CardBatch) -> UpsertResult:
        return store.upsert(batch.cards)

    @app.get("/cards/{card_id}")
    def card(card_id: str) -> Card:
        found = store.get(card_id)
        if found is None:
            raise HTTPException(404, "unknown card")
        return found

    @app.post("/search")
    def search(request: SearchRequest) -> SearchResponse:
        return SearchResponse(results=store.search(request))

    @app.post("/ingestion-runs", status_code=204)
    def ingestion_run(run: IngestionRun) -> None:
        store.record_run(run)

    @app.get("/stats")
    def stats() -> Stats:
        return store.stats()

    return app


app = create_app()

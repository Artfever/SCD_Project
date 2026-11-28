"""M5 Tool Layer: the single controlled exit to the internet."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from src.config import Settings, load_settings
from src.fetcher import Fetcher, FetchResult, TooLargeError, UpstreamError
from src.policy import PolicyError

SERVICE = "tools"
METRICS = ("requests", "cache_hits", "robots_blocked", "upstream_errors", "blocked_injections")


class FetchRequest(BaseModel):
    url: str = Field(max_length=2000)


def create_app(
    settings: Settings | None = None, transport: httpx2.AsyncBaseTransport | None = None
) -> FastAPI:
    settings = settings or load_settings(os.environ)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with httpx2.AsyncClient(
            transport=transport, timeout=settings.timeout, follow_redirects=False
        ) as client:
            app.state.fetcher = Fetcher(settings, client)
            yield

    app = FastAPI(title=f"scd-{SERVICE}", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness: the process is running."""
        return {"status": "ok", "service": SERVICE}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        """Readiness: the service has no dependency it must wait for."""
        return {"status": "ready", "service": SERVICE}

    @app.post("/fetch")
    async def fetch(request: FetchRequest) -> FetchResult:
        fetcher: Fetcher = app.state.fetcher
        try:
            return await fetcher.fetch(request.url)
        except PolicyError as error:
            raise HTTPException(403, str(error)) from error
        except TooLargeError as error:
            raise HTTPException(413, str(error)) from error
        except UpstreamError as error:
            raise HTTPException(502, str(error)) from error

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> str:
        fetcher: Fetcher = app.state.fetcher
        return "".join(f"tools_{name}_total {fetcher.metrics[name]}\n" for name in METRICS)

    return app


app = create_app()

"""M4 Scout agents: on-demand collection. Scheduled runs use `src.cli`."""

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.runner import RunSummary, run_source
from src.toolclient import ToolClient

SERVICE = "scouts"


class RunRequest(BaseModel):
    source: Literal["hackernews", "github", "devto"]
    months: int = Field(default=1, ge=1, le=24)
    pages: int = Field(default=1, ge=1, le=10)


def create_app(client: ToolClient | None = None, data_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title=f"scd-{SERVICE}")
    tools = client or ToolClient(os.environ.get("TOOLS_URL", "http://tools:8000"))
    folder = data_dir or Path(os.environ.get("DATA_DIR", "data"))

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness: the process is running."""
        return {"status": "ok", "service": SERVICE}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        """Readiness: a failing source or tool layer is reported per run, not here."""
        return {"status": "ready", "service": SERVICE}

    @app.post("/run")
    def run(request: RunRequest) -> RunSummary:
        return run_source(request.source, tools, folder, request.months, request.pages)

    return app


app = create_app()

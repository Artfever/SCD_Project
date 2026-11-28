"""M11 Verdict Engine: service skeleton."""

from fastapi import FastAPI

SERVICE = "verdict"

app = FastAPI(title=f"scd-{SERVICE}")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is running."""
    return {"status": "ok", "service": SERVICE}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness: check dependencies here once the service has any."""
    return {"status": "ready", "service": SERVICE}

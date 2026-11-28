from fastapi.testclient import TestClient

from src.database import Database
from src.main import create_app
from src.repository import Repository

# Port 1 has no database behind it
client = TestClient(create_app(Repository(Database("postgresql://nobody@127.0.0.1:1/none"))))


def test_health_does_not_need_the_database() -> None:
    response = client.get("/health")
    assert response.json() == {"status": "ok", "service": "kb"}


def test_ready_reports_a_missing_database() -> None:
    assert client.get("/ready").status_code == 503


def test_invalid_input_is_rejected_before_the_database() -> None:
    assert client.post("/search", json={"query": ""}).status_code == 422
    assert client.post("/cards", json={"cards": [{"id": "x"}]}).status_code == 422

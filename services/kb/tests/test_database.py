from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from src.main import create_app
from src.repository import Repository
from src.seed import load_fixture


def test_migrations_run_once(repository: Repository) -> None:
    assert repository.database.migrate()
    assert repository.database.migrate() == []


def test_upsert_is_repeatable_without_duplicates(repository: Repository) -> None:
    cards = load_fixture()
    assert repository.upsert(cards).added == len(cards)
    again = [card.model_copy(update={"fetched_at": datetime.now(UTC)}) for card in cards]
    assert repository.upsert(again).unchanged == len(cards)
    changed = cards[0].model_copy(update={"chunks": ["New text about exports"]})
    assert repository.upsert([changed]).updated == 1
    stats = repository.stats()
    assert stats.cards == len(cards)
    assert stats.chunks == 2 * len(cards) - 1


def test_search_returns_ranked_evidence_with_ids(repository: Repository) -> None:
    repository.upsert(load_fixture())
    client = TestClient(create_app(repository))
    assert client.get("/ready").status_code == 200
    results = client.post("/search", json={"query": "flashcards for students"}).json()["results"]
    assert {"CardForge", "StudyLoop"} <= {r["name"] for r in results}
    assert all(r["evidence_id"].startswith(r["card_id"] + "#c") for r in results)
    assert len({r["card_id"] for r in results}) == len(results)
    assert [r["score"] for r in results] == sorted((r["score"] for r in results), reverse=True)


def test_search_filters(repository: Repository) -> None:
    repository.upsert(load_fixture())
    client = TestClient(create_app(repository))

    def names(**filters: object) -> set[str]:
        body = {"query": "students revision flashcards quiz export"} | filters
        return {r["name"] for r in client.post("/search", json=body).json()["results"]}

    assert names(sources=["github"]) <= {"QuizNest", "LedgerLite", "QueueCheck"}
    assert names(niche="devtools") == {"ExportPal"}
    assert names(published_after=str(date(2027, 1, 1))) == set()


def test_search_text_is_not_executed(repository: Repository) -> None:
    repository.upsert(load_fixture())
    client = TestClient(create_app(repository))
    for query in ["'); DROP TABLE cards; --", "the and of", "a | b & !c"]:
        assert client.post("/search", json={"query": query}).status_code == 200
    assert repository.stats().cards == 8


def test_card_lookup_and_ingestion_run(repository: Repository) -> None:
    repository.upsert(load_fixture())
    client = TestClient(create_app(repository))
    assert client.get("/cards/card_seed01").json()["name"] == "ExportPal"
    assert client.get("/cards/card_missing").status_code == 404
    run = {"run_id": "r1", "source": "github", "added": 3, "dropped": 1}
    assert client.post("/ingestion-runs", json=run).status_code == 204
    assert client.post("/ingestion-runs", json=run).status_code == 204

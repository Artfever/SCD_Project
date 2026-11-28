import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx2

from src.cards import CHUNK_CHARS, RawItem, build_cards, canonical_url, split_chunks
from src.cli import main, read_snapshot, write_snapshot

NOW = datetime(2026, 11, 28, tzinfo=UTC)


def item(**changes: Any) -> RawItem:
    values: dict[str, Any] = {
        "source": "github",
        "external_id": "1",
        "title": "exporter",
        "summary": "Exports boards to spreadsheets quickly",
        "text": "I was tired of slow exports. This fixes it.",
        "url": "https://github.com/o/Exporter",
        "published_at": date(2026, 10, 2),
        "fetched_at": NOW,
        "tags": ["Productivity", "showdev"],
    }
    return RawItem.model_validate(values | changes)


def test_canonical_url() -> None:
    variants = [
        "https://github.com/o/Exporter/",
        "http://www.github.com/o/exporter.git",
        "https://github.com/o/exporter?utm_source=x#readme",
    ]
    assert {canonical_url(url) for url in variants} == {"github.com/o/exporter"}
    assert canonical_url("https://a.dev/p?id=2") != canonical_url("https://a.dev/p?id=3")


def test_same_page_from_two_platforms_is_one_card_with_both_sources() -> None:
    other = item(
        source="hackernews",
        external_id="9",
        title="Exporter",
        url="https://github.com/o/exporter/",
        published_at=date(2026, 10, 5),
        tags=[],
    )
    cards, dropped = build_cards([item(), other])
    (card,) = cards
    assert card.source == "github"
    assert [ref.source for ref in card.also_seen] == ["hackernews"]
    assert dropped == {"hackernews": 1}
    assert card.niche_tags == ["productivity"]
    assert card.problem == "I was tired of slow exports."


def test_same_title_and_description_on_another_address_is_merged() -> None:
    other = item(source="devto", external_id="2", url="https://dev.to/o/exporter")
    cards, _ = build_cards([item(), other])
    assert len(cards) == 1


def test_repeated_snapshot_of_one_item_is_not_a_drop() -> None:
    later = item(fetched_at=NOW + timedelta(days=1), summary="Exports boards faster than before")
    cards, dropped = build_cards([later, item()])
    assert cards[0].summary == "Exports boards faster than before"
    assert not dropped


def test_card_ids_are_stable_and_empty_items_are_dropped() -> None:
    first, _ = build_cards([item()])
    second, dropped = build_cards(
        [item(), item(external_id="2", title="x", summary="", text="", url="https://a.dev/x")]
    )
    assert [card.id for card in first] == [card.id for card in second]
    assert dropped == {"github": 1}


def test_chunks_are_bounded_and_overlap_by_one_sentence() -> None:
    text = " ".join(f"Sentence number {n} describes one more feature." for n in range(60))
    chunks = split_chunks(text)
    assert len(chunks) > 1
    assert all(len(chunk) <= CHUNK_CHARS for chunk in chunks)
    assert chunks[1].startswith(chunks[0].split(". ")[-1][:20])
    assert "number 59" in chunks[-1]
    assert split_chunks("x" * 2000)[0] == "x" * CHUNK_CHARS
    assert split_chunks("") == []


def test_snapshot_round_trip_is_deterministic(tmp_path: Path) -> None:
    cards, _ = build_cards([item(text="Unicode   separator stays inside one line.")])
    first, second = tmp_path / "a.jsonl.gz", tmp_path / "b.jsonl.gz"
    write_snapshot(cards, first)
    write_snapshot(cards, second)
    assert first.read_bytes() == second.read_bytes()
    assert read_snapshot(first) == cards


def test_job_indexes_and_records_the_run(tmp_path: Path, monkeypatch: Any) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "github-1.jsonl").write_text(item().model_dump_json() + "\nnot json\n", "utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    calls: list[tuple[str, Any]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append((request.url.path, json.loads(request.content)))
        if request.url.path == "/cards":
            return httpx2.Response(200, json={"added": 1, "updated": 0, "unchanged": 0})
        return httpx2.Response(204)

    client = httpx2.Client(base_url="http://kb", transport=httpx2.MockTransport(handler))
    assert main([], client) == 0
    assert [path for path, _ in calls] == ["/cards", "/ingestion-runs"]
    assert calls[1][1]["added"] == 1


def test_job_fails_without_data_or_knowledge_base(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert main([]) == 1
    snapshot = tmp_path / "s.jsonl.gz"
    write_snapshot(build_cards([item()])[0], snapshot)
    failing = httpx2.MockTransport(lambda _: httpx2.Response(503))
    client = httpx2.Client(base_url="http://kb", transport=failing)
    assert main(["--from-snapshot", str(snapshot)], client) == 1

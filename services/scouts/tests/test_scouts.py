import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import httpx2
from fastapi.testclient import TestClient

from src import cli
from src.items import clean
from src.main import create_app
from src.runner import run_source
from src.sources import Window, month_ranges, parse_devto, parse_github, parse_hn
from src.toolclient import ToolClient

HN = {
    "hits": [
        {
            "objectID": "1",
            "title": "Show HN: Exporter",
            "url": None,
            "story_text": "<p>Mail me at a.b@example.com &amp; try it</p>",
            "created_at": "2026-10-03T10:00:00Z",
            "points": 12,
            "author": "someone",
        }
    ]
}


def tool_layer(answer: Callable[[str], Any]) -> ToolClient:
    def handler(request: httpx2.Request) -> httpx2.Response:
        url = json.loads(request.content)["url"]
        result = answer(url)
        if isinstance(result, httpx2.Response):
            return result
        return httpx2.Response(200, json={"status": 200, "body": json.dumps(result)})

    return ToolClient("http://tools:8000", httpx2.MockTransport(handler))


def test_clean_removes_markup_and_contact_details() -> None:
    assert clean("<b>Call +92 300 1234567</b> or x@y.io") == "Call [phone] or [email]"


def test_hn_item_has_no_author_and_falls_back_to_discussion_url() -> None:
    (item,) = parse_hn(HN)
    assert item.title == "Exporter"
    assert item.url == "https://news.ycombinator.com/item?id=1"
    assert item.text == "Mail me at [email] & try it"
    assert "someone" not in item.model_dump_json()


def test_github_skips_forks_and_empty_descriptions() -> None:
    base = {"id": 1, "name": "a", "html_url": "https://github.com/o/a", "fork": False}
    base |= {"created_at": "2026-10-01T00:00:00Z", "description": "Does a", "language": "Go"}
    document = {"items": [base, base | {"id": 2, "fork": True}, base | {"description": None}]}
    (item,) = parse_github(document)
    assert item.tags == ["go"]


def test_devto_article() -> None:
    article = {
        "id": 5,
        "title": "My tool",
        "description": "It helps",
        "url": "https://dev.to/x/my-tool",
        "published_at": "2026-09-01T00:00:00Z",
        "tag_list": ["showdev"],
    }
    assert parse_devto([article])[0].summary == "It helps"


def test_month_ranges_cross_a_year() -> None:
    ranges = list(month_ranges(Window(months=3, pages=1, today=date(2027, 1, 15))))
    assert ranges[0] == (date(2027, 1, 1), date(2027, 2, 1))
    assert ranges[2] == (date(2026, 11, 1), date(2026, 12, 1))


def test_run_writes_snapshot_and_stops_after_short_page(tmp_path: Path) -> None:
    summary = run_source("hackernews", tool_layer(lambda _: HN), tmp_path, 2, 5)
    assert (summary.items, summary.requests, summary.failures) == (1, 2, 0)
    assert summary.file is not None
    lines = Path(summary.file).read_text("utf-8").splitlines()
    assert json.loads(lines[0])["source"] == "hackernews"
    assert not list(tmp_path.rglob("*.part"))


def test_one_failing_page_does_not_stop_the_source(tmp_path: Path) -> None:
    calls: list[str] = []

    def answer(url: str) -> Any:
        calls.append(url)
        return httpx2.Response(502, text="upstream") if len(calls) == 1 else HN

    summary = run_source("hackernews", tool_layer(answer), tmp_path, 3, 1)
    assert (summary.items, summary.failures, summary.aborted) == (1, 1, False)


def test_source_is_abandoned_after_repeated_failures(tmp_path: Path) -> None:
    client = tool_layer(lambda _: {"unexpected": True})
    summary = run_source("github", client, tmp_path, 12, 1)
    assert (summary.requests, summary.aborted, summary.file) == (3, True, None)


def test_empty_source(tmp_path: Path) -> None:
    summary = run_source("devto", tool_layer(lambda _: []), tmp_path, 6, 1)
    assert (summary.items, summary.requests, summary.file) == (0, 1, None)


def test_on_demand_run(tmp_path: Path) -> None:
    app = create_app(tool_layer(lambda _: HN), tmp_path)
    response = TestClient(app).post("/run", json={"source": "hackernews"})
    assert response.json()["items"] == 1
    assert TestClient(app).post("/run", json={"source": "reddit"}).status_code == 422


def test_cli_fails_when_a_source_gives_nothing(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setattr(cli, "ToolClient", lambda _: tool_layer(lambda _: []))
    assert cli.main(["--source", "devto"]) == 1
    monkeypatch.setattr(cli, "ToolClient", lambda _: tool_layer(lambda _: HN))
    assert cli.main(["--source", "hackernews"]) == 0

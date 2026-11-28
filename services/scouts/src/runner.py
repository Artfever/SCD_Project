"""Run one source, survive failing pages, and write a snapshot file."""

import logging
from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import BaseModel, ValidationError

from src.items import RawItem
from src.sources import PER_PAGE, SOURCES, Window
from src.toolclient import SourceError, ToolClient

log = logging.getLogger("scouts")

# Give up on a source after this many failures in a row
MAX_CONSECUTIVE_FAILURES = 3


class RunSummary(BaseModel):
    source: str
    items: int
    requests: int
    failures: int
    aborted: bool
    file: str | None


def run_source(
    source: str,
    client: ToolClient,
    data_dir: Path,
    months: int,
    pages: int,
    today: date | None = None,
) -> RunSummary:
    window = Window(months=months, pages=pages, today=today or datetime.now(UTC).date())
    found: dict[str, RawItem] = {}
    finished: set[str] = set()
    requests = failures = streak = 0
    for page in SOURCES[source](window):
        if page.group in finished:
            continue
        requests += 1
        try:
            document = page.parse(client.get_json(page.url))
        except (SourceError, KeyError, TypeError, ValidationError) as error:
            failures += 1
            streak += 1
            log.warning("%s: page failed: %s", source, error)
            if streak >= MAX_CONSECUTIVE_FAILURES:
                break
            continue
        streak = 0
        for item in document:
            found[item.external_id] = item
        # Parsers drop unusable entries, so only a clearly short page ends the group
        if len(document) < PER_PAGE // 2:
            finished.add(page.group)
    return RunSummary(
        source=source,
        items=len(found),
        requests=requests,
        failures=failures,
        aborted=streak >= MAX_CONSECUTIVE_FAILURES,
        file=_write(data_dir, source, list(found.values())),
    )


def _write(data_dir: Path, source: str, items: list[RawItem]) -> str | None:
    if not items:
        return None
    folder = data_dir / "raw"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = folder / f"{source}-{stamp}.jsonl"
    # Write to a temporary name so ingestion never reads half a file
    partial = target.with_suffix(".part")
    partial.write_text("".join(item.model_dump_json() + "\n" for item in items), "utf-8")
    partial.replace(target)
    return str(target)

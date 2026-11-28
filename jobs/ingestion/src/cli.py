"""M6i ingestion job: `python -m src.cli` reads raw snapshots and indexes cards in M6."""

import argparse
import gzip
import logging
import os
import sys
import uuid
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

import httpx2
from pydantic import ValidationError

from src.cards import Card, RawItem, build_cards

BATCH = 100
log = logging.getLogger("ingestion")


def read_raw(data_dir: Path) -> Iterator[RawItem]:
    for path in sorted((data_dir / "raw").glob("*.jsonl")):
        for number, line in enumerate(path.read_text("utf-8").splitlines(), start=1):
            try:
                yield RawItem.model_validate_json(line)
            except ValidationError:
                log.warning("skipping invalid line %s:%d", path.name, number)


def write_snapshot(cards: list[Card], path: Path) -> None:
    """Compressed card data, identical bytes for identical cards."""
    lines = "".join(card.model_dump_json() + "\n" for card in sorted(cards, key=lambda c: c.id))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(lines.encode(), mtime=0))


def read_snapshot(path: Path) -> list[Card]:
    text = gzip.decompress(path.read_bytes()).decode()
    return [Card.model_validate_json(line) for line in text.split("\n") if line]


def index(
    cards: list[Card], dropped: Counter[str], client: httpx2.Client
) -> dict[str, Counter[str]]:
    """Send cards to the knowledge base source by source and record each run."""
    run_id = uuid.uuid4().hex
    totals: dict[str, Counter[str]] = {}
    for source in sorted({card.source for card in cards} | set(dropped)):
        selected = [card for card in cards if card.source == source]
        total: Counter[str] = Counter(added=0, updated=0, unchanged=0)
        for start in range(0, len(selected), BATCH):
            batch = [card.model_dump(mode="json") for card in selected[start : start + BATCH]]
            response = client.post("/cards", json={"cards": batch})
            response.raise_for_status()
            total.update(response.json())
        record = {"run_id": run_id, "source": source, "dropped": dropped[source], **total}
        client.post("/ingestion-runs", json=record).raise_for_status()
        total["dropped"] = dropped[source]
        totals[source] = total
    return totals


def main(argv: list[str] | None = None, client: httpx2.Client | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build idea cards and index them")
    parser.add_argument("--snapshot", type=Path, help="also write the cards to this .jsonl.gz")
    parser.add_argument("--from-snapshot", type=Path, help="index a snapshot instead of raw files")
    parser.add_argument("--no-index", action="store_true", help="do not call the knowledge base")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    dropped: Counter[str] = Counter()
    if args.from_snapshot:
        cards = read_snapshot(args.from_snapshot)
    else:
        cards, dropped = build_cards(read_raw(Path(os.environ.get("DATA_DIR", "data"))))
    if not cards:
        log.error("no cards to index")
        return 1
    per_source = Counter(card.source for card in cards)
    log.info("%d cards %s, dropped or merged %s", len(cards), dict(per_source), dict(dropped))
    if args.snapshot:
        write_snapshot(cards, args.snapshot)
    if args.no_index:
        return 0
    http = client or httpx2.Client(base_url=os.environ.get("KB_URL", "http://kb:8000"), timeout=300)
    try:
        for source, total in index(cards, dropped, http).items():
            log.info("%s %s", source, dict(total))
    except httpx2.HTTPError as error:
        log.error("knowledge base failed: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

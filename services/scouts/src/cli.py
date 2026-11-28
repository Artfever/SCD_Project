"""Scheduled use: `python -m src.cli --source hackernews` (Kubernetes CronJob)."""

import argparse
import logging
import os
import sys
from pathlib import Path

from src.runner import run_source
from src.sources import SOURCES
from src.toolclient import ToolClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect raw items from one or all sources")
    parser.add_argument("--source", choices=[*SOURCES, "all"], default="all")
    parser.add_argument("--months", type=int, default=2, help="months back to look")
    parser.add_argument("--pages", type=int, default=2, help="page budget per month")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    client = ToolClient(os.environ.get("TOOLS_URL", "http://tools:8000"))
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    names = list(SOURCES) if args.source == "all" else [args.source]
    broken = 0
    try:
        for name in names:
            summary = run_source(name, client, data_dir, args.months, args.pages)
            print(summary.model_dump_json(), flush=True)
            broken += summary.items == 0
    finally:
        client.close()
    # A job fails only when a source gave nothing at all
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())

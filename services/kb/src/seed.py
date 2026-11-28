"""Load the example cards for development: `python -m src.seed`. The cards are invented."""

import json
from pathlib import Path

from src.database import Database
from src.models import CardWithChunks
from src.repository import Repository

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "seed_cards.jsonl"


def load_fixture(path: Path = FIXTURE) -> list[CardWithChunks]:
    cards = []
    for line in path.read_text("utf-8").splitlines():
        data = json.loads(line)
        data["chunks"] = [f"{data['name']}. {data['summary']}", data["text"]]
        cards.append(CardWithChunks.model_validate(data))
    return cards


if __name__ == "__main__":
    print(Repository(Database()).upsert(load_fixture()).model_dump_json())

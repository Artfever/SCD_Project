# M6i Ingestion jobs

Owner: `Artfever`. Issue #14.

Reads `DATA_DIR/raw/*.jsonl` from the scouts, builds idea cards and sends them to the knowledge base.

- **Dedupe:** one card per canonical URL; the same title and description elsewhere is merged. Every
  place a card was seen is kept as a source.
- **Chunking:** name and summary first, then about 600 characters per chunk with one sentence of
  overlap. Embedding belongs to M6, so only one copy of the model is loaded.
- **Repeatable:** ids come from the URL; unchanged cards are not rewritten.
- `problem` is the first complaint-like sentence (a heuristic). `customer` stays empty.

```bash
python -m src.cli                                            # raw files -> knowledge base
python -m src.cli --snapshot snapshot/cards.jsonl.gz         # also refresh the committed snapshot
python -m src.cli --from-snapshot snapshot/cards.jsonl.gz    # load the snapshot, no scouting
```

With Compose, from the repository root:

```bash
docker compose --profile app up -d --build kb
docker compose run --rm --build ingestion python -m src.cli --from-snapshot snapshot/cards.jsonl.gz
```

The snapshot holds public titles, descriptions and links from Hacker News, GitHub and DEV.to. Every
card keeps its source and URL.

| Variable | Default |
| --- | --- |
| `KB_URL` | `http://kb:8000` |
| `DATA_DIR` | `/data` in the container |

## Snapshot of 2026-11-28

| Source | Cards |
| --- | --- |
| Hacker News | 3,715 |
| GitHub | 3,418 |
| DEV.to | 2,118 |
| **Total** | **9,251** (120 seen in more than one place, 725 with a complaint sentence) |

Collected for the previous twelve months. A second load added and changed nothing.

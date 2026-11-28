# M6 Knowledge Base

Owner: `Artfever`. Work is tracked in #8, #15.

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /search` | `{"query", "k", "sources", "niche", "published_after", "published_before"}` returns evidence items with ids |
| `POST /cards` | Insert or update up to 200 cards with their chunks (used by ingestion) |
| `GET /cards/{id}` | One card |
| `POST /ingestion-runs` | Record the result of a run |
| `GET /stats` | Cards per source and how fresh they are |
| `GET /ready` | 503 until the database answers and is migrated |

Evidence ids are `<card id>#c<chunk number>`. Interactive docs are at `/docs`.

## Develop against it

```bash
docker compose --profile app up -d --build kb       # API on http://127.0.0.1:8001
docker compose exec kb python -m src.seed            # 8 invented example cards
curl -s http://127.0.0.1:8001/search -H 'content-type: application/json'   -d '{"query":"flashcards for students"}'
```

Database tests need `TEST_DATABASE_URL` (see `tests/conftest.py`).

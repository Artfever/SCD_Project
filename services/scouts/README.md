# M4 Scout agents

Owner: `Artfever`. Work is tracked in #13.

## Sources

| Source | API | Collected |
| --- | --- | --- |
| `hackernews` | HN Search API (Algolia), `show_hn` posts with 10 or more points | title, post text, link, date, points |
| `github` | GitHub REST search, repositories with 50 or more stars by creation month | name, description, topics, link, date, stars |
| `devto` | Forem API, `showdev` articles | title, description, tags, link, date, reactions |

All requests go through M5, which enforces the rate limits and robots.txt. Author names are not
collected; e-mail addresses and phone numbers are replaced.

The YC directory is not collected: its listing pages are disallowed by `robots.txt`, and the public
mirror is unofficial.

## Use

- On demand: `POST /run` with `{"source": "github", "months": 1, "pages": 1}`
- Scheduled: `python -m src.cli --source all --months 12 --pages 5`

Output: `DATA_DIR/raw/<source>-<timestamp>.jsonl`, read by ingestion. One failing page is skipped;
a source is abandoned after three failures in a row.

| Variable | Default |
| --- | --- |
| `TOOLS_URL` | `http://tools:8000` |
| `DATA_DIR` | `/data` in the container |

# M5 Tool Layer

Owner: `Artfever`. Work is tracked in #9.

## API

`POST /fetch` with `{"url": "https://..."}` returns `url`, `final_url`, `status`, `content_type`,
`body` (sanitised text, or sanitised JSON as a string), `fetched_at`, `cached` and `removed` (number
of instruction-like segments taken out). Errors: 403 rule broken, 413 too large, 502 upstream
failure. `GET /metrics` gives counters.

## Rules

- https on port 443 to hosts on the allow-list only; redirects are checked the same way.
- robots.txt is honoured (RFC 9309 matching). If it cannot be read, the site is not fetched.
- Minimum interval per host, retries with back-off, `Retry-After` respected.
- Responses cached in memory for an hour; at most 5 MB.
- The sanitiser is pattern based. It lowers risk but does not remove it: consumers must still treat
  fetched text as data.

## Settings

| Variable | Meaning |
| --- | --- |
| `ALLOWED_DOMAINS` | `host=seconds` pairs, comma separated (`config/tools.env`) |
| `CACHE_TTL_SECONDS` | Cache lifetime |
| `GITHUB_TOKEN` | Optional, sent to `api.github.com` only |

# F-022 — No persistent DB connections (CONN_MAX_AGE=0) — worth lens

**Verdict:** CONFIRMED (fact and fix correct; severity overstated)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/config/settings.py:107-116`: `DATABASES["default"]` sets no `CONN_MAX_AGE`, so Django's default 0 applies: one new Postgres connection per request.
- Per-request queries are real but few: `middleware.py:16` (PageView update), `context_processors.py:10,15,29` (count, PageView, PortfolioProfile).
- Impact is small: DB is on the same Docker network (`infra/docker-compose.prod.yml`, `DB_HOST=db`), no TLS handshake; low-traffic portfolio site. Saves a few ms per request, not a real bottleneck -> low, not medium.
- Change is safe: gunicorn runs with default 1 sync worker (`infra/docker-compose.prod.yml:46`, no `--workers/--threads`), Celery prefork default concurrency. Connection count stays tiny, so the "max_connections" risk is moot. Celery's Django fixup calls `close_old_connections` around tasks and honours `CONN_MAX_AGE`. SQLite (dev default, `settings.py:109`) ignores it harmlessly.
- No doc or git log entry indicates a deliberate choice of `CONN_MAX_AGE=0` (git log grep for conn/connection/postgres: nothing relevant).

## Better proposal
Skip the new `DB_CONN_MAX_AGE` env var (config nobody needs). Hardcode in `DATABASES["default"]`:
```python
"CONN_MAX_AGE": 60,
"CONN_HEALTH_CHECKS": True,
```
Effort S. Optional; fine to defer.

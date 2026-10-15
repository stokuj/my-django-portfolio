# F-022 — No persistent DB connections (CONN_MAX_AGE=0)

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/config/settings.py:109-118`: `DATABASES["default"]` sets only ENGINE/NAME/USER/PASSWORD/HOST/PORT. No `CONN_MAX_AGE` or `CONN_HEALTH_CHECKS` anywhere in the repo (grep over *.py, *.yml, *.toml, .env.example). Django default is 0, so each request opens and closes its own Postgres connection.
- Per-request queries are real: context processors `django/main/context_processors.py:10` (Project count), `:15` (PageView), `:29` (PortfolioProfile), registered at `settings.py:79-81`; plus session/auth lookups and `django/main/middleware.py:15-16` on home visits. "3-6 queries" is plausible.
- Risk note is moot in practice: `infra/docker-compose.prod.yml:46` runs `gunicorn config.wsgi:application` with default settings (1 sync worker, no threads), so persistent connections add at most one connection per web process.

## Why severity is lowered
Low-traffic portfolio, Postgres on the same Docker network: connection setup costs a few ms per request. Correct observation, cheap fix, but not a medium-impact performance problem.

## Proposal
Fine as stated, simpler without a new env var:
`"CONN_MAX_AGE": 60, "CONN_HEALTH_CHECKS": True` in `DATABASES["default"]`. Effort S.

# F-051 — Celery 5.4.0 does not support Python 3.13 (worth lens)

**Verdict:** CONFIRMED (not refuted)
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `pyproject.toml:5` pins `requires-python = ">=3.13,<3.14"`; `infra/Dockerfile:10` uses `FROM python:3.13-slim`.
- `pyproject.toml:9` pins `celery[redis]==5.4.0`. PyPI metadata (checked 2026-10-15): 5.4.0 classifiers stop at 3.12; latest is 5.6.3 with a 3.13 classifier. The facts in the finding are correct.
- No sign of a deliberate decision to stay on 5.4: git log shows the pin unchanged since `335e524`, and the dependency audit `667e27f` did not touch it. Nothing in docs/ mentions it.
- The local venv already resolves `kombu 5.6.2` and `billiard 4.2.4` under `celery 5.4.0`, so the transport layer is already newer than the core. A bump brings them back in line.
- Why the severity drops: there is no observed failure. Celery worker, beat and app modules import cleanly on Python 3.13.12 with `-W error::DeprecationWarning`, and the prod stack runs on this combination. This is "officially unsupported", not "broken". It is hygiene, not a medium bug.
- Config used (`django/config/settings.py:203-214`: json serializers, `BROKER_CONNECTION_RETRY_ON_STARTUP`, `TASK_IGNORE_RESULT`, crontab beat schedule) is stable API across 5.4 to 5.6, so the bump is low risk.
- Could not run `main.tests.test_tasks` locally because no Postgres is reachable. CI `make verify` would cover it.

## Better proposal
Same fix, smallest diff: change `pyproject.toml:9` to `celery[redis]==5.6.3`, run `uv lock`, then `make verify`. Batch it with other dependency bumps instead of opening a separate PR.

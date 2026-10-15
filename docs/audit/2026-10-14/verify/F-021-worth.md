# F-021 (worth): Placeholder SECRET_KEY / DEBUG=True never caught; check --deploy not run

**Verdict:** CONFIRMED (with a corrected proposal)
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/config/settings.py:35-37` rejects only an empty `SECRET_KEY`. `DEBUG` defaults to False (`settings.py:40`). The hardening block only applies `if not DEBUG` (`settings.py:98-105`).
- `.env.example:2` sets `DJANGO_DEBUG=True` and `.env.example:5` sets a 30-char placeholder key. `make verify` runs a plain `check` with DEBUG=True (`Makefile:36`). The deploy script goes pull -> down -> up and never runs `check --deploy` (`.github/workflows/docker-build-push.yml:107-109`).
- Verified locally: with the placeholder key and DEBUG=True, `check --deploy` reports W004/W008/W009/W012/W016/W018. With a random 80-char key, DEBUG=False and a real host, `check --deploy --fail-level WARNING` passes cleanly ("no issues"). So the gate would not block the current correct config.
- Why the severity drops: the copy-from-example path is dev-only. `infra/scripts/ensure_env.py` only creates `.env` in `dev` mode, and `make prod-up` refuses to run without `.env` (`Makefile:22`). The prod `.env` on the droplet is written by hand. The risk is a human copying the example, which is a guardrail concern, not an existing hole.
- No conflict with existing tests: `tests/test_operational_files.py:79-95` only asserts that `down --remove-orphans` exists and that prune runs after `up`.

## Problems with the proposal as written
1. "Before `up`" is ambiguous. If the check runs between `down` (line 108) and `up` (line 109), a failure under `script_stop: true` leaves the site down. It must run after `pull` and before `down`, so a failure aborts with the old stack still serving.
2. `run --rm web` goes through the web entrypoint `wait-for-db.sh` (`docker-compose.prod.yml:42`), which needs the database and starts the `depends_on` services. `check --deploy` needs neither, so pass `--no-deps --entrypoint ""` to skip both.

## Better proposal
Insert after line 107 (`pull`) and before `down`:
```
docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml run --rm --no-deps --entrypoint "" web python manage.py check --deploy --fail-level WARNING
```
`python` is on PATH (system install, `infra/Dockerfile`), and `working_dir` is `/app/django` (`docker-compose.prod.yml:41`). Effort: S. Run it once by hand on the droplet first.

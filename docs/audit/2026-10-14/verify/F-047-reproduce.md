# F-047 - App service and logging blocks repeated 6x across compose files

**Lens:** reproduce
**Verdict:** CONFIRMED (with minor overstatements)
**Confidence:** high
**Adjusted severity:** low (pure duplication, no runtime defect)

## Reasoning

Verified at HEAD:

- Prod: identical 12-line `environment:` list in web/worker/beat at `infra/docker-compose.prod.yml:53-64`, `92-103`, `130-141`. Same `build/image/user/env_file/working_dir` header at `34-41`, `77-85`, `117-125`.
- Dev: same 12-line block at `infra/docker-compose.dev.yml:40-51`, `74-85`, `107-118`, same headers at `23-30`, `59-67`, `94-102`.
- Prod `logging:` block (5 lines) repeated 6x: `infra/docker-compose.prod.yml:16`, `27`, `70`, `110`, `147`, `174`. Dev has no logging blocks.
- `SECRET_KEY`, `DJANGO_DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` are passed via `env_file: ../.env` (prod `39-40`, `83-84`, `123-124`) under the same names read by `django/config/settings.py:35,40,43,107`, and interpolated from the same `.env` (`Makefile:3-4` `--env-file .env`). So those 4 lines are redundant. The `DB_*` remap (`DOCKER_DB_*` -> `DB_*`) and `CELERY_*` (redis hostnames) are not redundant.
- `GITHUB_HEATMAP_TOKEN` (`.env.example:12`, `settings.py:172`) reaches web, worker and beat via `env_file`. Not "every container": db, redis and caddy do not load `../.env`.
- Risk is real: `tests/test_operational_files.py:51-52` (`context: ..` count == 3), `:56` (`- ../.env` count == 3), `:72` (`    logging:` count == 6) are text-count tests that an anchor refactor breaks.

## Overstatements / caveats

- "Repeated 6x across compose files": YAML anchors do not cross files, so each file still keeps one copy (dedup is 3x -> 1x per file, logging 6x -> 1x in prod only). Sharing across dev/prod would need `extends`/`include` and a base file, which is more structure than the duplication warrants.
- Prod `web` has no `restart:` while worker/beat have `restart: always` (`prod.yml:82,122`). Putting `restart` in `x-app` would silently change web's behaviour; the proposed `docker compose config` diff catches this, keep it as the gate.
- Line saving: roughly 60-80 net, not 100, after adding the anchor definitions.

## Better proposal

Per file: `x-logging: &logging` (prod only) and `x-app: &app` with build/image/user/env_file/working_dir plus `environment` reduced to `DB_*` remap and `CELERY_*` (drop the 4 lines duplicated by env_file). Keep `restart`, `command`, `volumes`, `depends_on` per service. Verify with `docker compose config` diff before/after (expect an identical resolved config), and rewrite the 3 count tests to assert on parsed `docker compose config` output or drop them. Effort S-M. Low priority: duplication is static and identical, so drift risk is the only cost.

# F-047 — App service and logging blocks repeated 6x across compose files (worth lens)

**Verdict:** CONFIRMED (partially; overstated). **Confidence:** high. **Adjusted severity:** low.

## What holds
- Duplication is real: web/worker/beat repeat build/image/user/env_file/working_dir and a 12-line `environment` block in prod (`infra/docker-compose.prod.yml:34-41,52-64`, `77-85,91-103`, `117-125,129-141`) and dev (`infra/docker-compose.dev.yml:23-30,39-51`, `59-67,73-85`, `94-102,106-118`). `logging` appears 6x in prod (`prod.yml:16,27,70,110,147,174`).
- `SECRET_KEY`, `DJANGO_DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` passthrough lines are redundant: `env_file: ../.env` (prod.yml:39-40) is the same file as `--env-file .env` used for interpolation (`Makefile:3-4`, `.github/workflows/docker-build-push.yml:107-109`). Verified: `docker compose config` with those 4 lines removed renders identical `environment` for all 6 services (temp copy, `.env.example` as input).
- The `DB_*=${DOCKER_DB_*}` remap is deliberate and must stay (`.env.example:22-39`: host `DB_HOST=localhost` vs container `DOCKER_DB_HOST=db`). Same for `CELERY_*` override (`.env.example:43-44` point to 127.0.0.1).

## What is wrong / overstated
- **GITHUB_HEATMAP_TOKEN claim is not addressed by the proposal.** The token reaches every app container via `env_file` (prod.yml:39,83,123), not via `environment`. Trimming `environment` changes nothing there. Mixing a security note into a simplification finding misleads; scoping secrets per service is a separate change (and would need dropping `env_file`).
- **Anchor is not behaviour-neutral.** Prod `web` has no `restart:` while worker/beat have `restart: always` (prod.yml:82,122; web 33-75 has none). A shared `x-app` must not include `restart`, or web silently gains a restart policy (arguably desirable, but it is a behaviour change hidden in a "refactor").
- **Breaks tests:** `tests/test_operational_files.py:49-51` (count of `context: ..` == 3), `54-56` (count of `- ../.env` == 3), `70-72` (count of `    logging:` == 6). Effort M is mostly test rewriting, not compose editing.
- Anchors cannot span the dev and prod files, so each file still carries its own copy; "6x across compose files" shrinks to 2 anchors, not 1.
- Severity medium is too high for a portfolio compose file with no runtime defect; this is low.

## Better proposal (smallest diff)
1. Delete the 4 redundant passthrough lines (`SECRET_KEY`, `DJANGO_DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`) from each of the 6 `environment` blocks: -24 lines, zero test changes, rendered config identical (verified). Effort S.
2. Optional: `x-logging: &logging` in prod only, plus updating the logging test (`tests/test_operational_files.py:70-72`) to parse YAML or `docker compose config`. Skip the `x-app` anchor unless F-053 rewrites the grep tests anyway; ~8 repeated lines per service is readable and explicit.
3. Handle GITHUB_HEATMAP_TOKEN scoping (if wanted) as its own security finding.

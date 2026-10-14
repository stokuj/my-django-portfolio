# ponytail-infra

Scope: infra/, tests/, Makefile, .github/, pyproject.toml, package.json, .dockerignore, .gitignore, docs/ at `dev` HEAD (4416049). Over-engineering lens: what to delete or simplify.

## 1. Obsolete plans/specs in docs/superpowers (~4.4k lines)
- Severity: medium | Category: docs | Effort: S
- File: docs/superpowers/plans/2026-05-14-codebase-audit.md:1 (and 10 sibling files)
- Problem: 6 plans + 5 specs (1257 + 926 + 885 + ... lines, 172K) for issues #51, #53, #55, #57 and the 2026-05 audit. All are merged work. They hold step-by-step task lists that no longer match the code, and they are what an agent finds first when it greps docs/.
- Proposal: delete `docs/superpowers/`. Git history keeps them. Leave lasting decisions in docs/architecture.md / implementation.md.
- Risk: none. Recover with `git show`.

## 2. Operational tests in tests/ are never run
- Severity: medium | Category: tests | Effort: S
- File: Makefile:39
- Problem: `verify` only runs ruff over `tests/`. Neither CI workflow runs them. CLAUDE.md:29 says `uv run python -m pytest tests/`, but pytest is not installed (`No module named pytest`). The 26 tests pass only under `python -m unittest discover -s tests -t .`.
- Proposal: if items 3-5 are applied, the directory goes away and nothing is left to wire up. If not, add `uv run python -m unittest discover -s tests -t .` to `verify` and fix CLAUDE.md:29.
- Risk: none.

## 3. compose_status.py rebuilds `docker ps --format table`
- Severity: medium | Category: simplification | Effort: S
- File: infra/scripts/compose_status.py:1
- Problem: 91 lines (JSON parse, column-width math) plus 3 tests (tests/test_operational_helpers.py:55-101) for output that `prod-status` already gets from one `docker ps --filter ... --format "table ..."` call (Makefile:28-31).
- Proposal: make `dev-status` the same `docker ps` line with `my-django-portfolio-dev`, or use `$(DEV_COMPOSE) ps`. Delete the script and its tests.
- Risk: none. Output differs only cosmetically.

## 4. ensure_env.py is 46 lines for `cp -n`
- Severity: medium | Category: simplification | Effort: S
- File: infra/scripts/ensure_env.py:1
- Problem: argparse, a dev/prod mode and 4 tests (tests/test_operational_helpers.py:9-52) for "copy .env.example to .env if missing". Nothing calls the prod mode: `prod-up` uses a shell guard (Makefile:22).
- Proposal: Makefile:7 becomes `@test -f .env || { cp .env.example .env && echo "Created .env from .env.example"; }`. Delete infra/scripts/ (including `__init__.py`, which exists only so tests can import it) and tests/test_operational_helpers.py. Drop `infra/scripts` from the ruff target (Makefile:39).
- Risk: none.

## 5. test_operational_files.py: string-grep change detectors
- Severity: medium | Category: tests | Effort: S
- File: tests/test_operational_files.py:51
- Problem: 19 tests check that files exist, that strings appear, and exact counts (`count("context: ..") == 3`, `count("    logging:") == 6`). They test no behaviour and fail on any harmless refactor, such as the YAML anchors in item 6.
- Proposal: delete the file and the empty tests/ package. For a real check, add `docker compose -f infra/docker-compose.prod.yml config -q` (with the CI .env) to CI. It validates the files rather than grepping them.
- Risk: you lose the reminder for the issue #55/#57 decisions (project name, prune order). Record them as one-line comments in the Makefile/workflow instead.

## 6. Compose files repeat the app service block 6 times
- Severity: medium | Category: simplification | Effort: M
- File: infra/docker-compose.prod.yml:52
- Problem: web/worker/beat repeat build/image/user/env_file/working_dir and the same 12-line `environment:` block. That is 3x in prod (52-64, 91-103, 129-141) and 3x in dev (39-51, 73-85, 106-118). The `logging:` block appears 6x in prod. SECRET_KEY, DJANGO_DEBUG, ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS are already loaded by `env_file: ../.env`. Only the DOCKER_DB_* -> DB_* remap and CELERY_* need `environment:`.
- Proposal: add top-level `x-app: &app` (build, image, user, env_file, working_dir, environment with only the DB_* and CELERY_* entries) and `x-logging: &logging`. Each service then uses `<<: *app` plus its command and volumes. Roughly -100 lines across both files.
- Risk: the tests in item 5 break (delete them). Run `docker compose config` before and after to confirm identical effective config.

## 7. Docker image ignores uv.lock and floats transitive deps
- Severity: medium | Category: library | Effort: S
- File: infra/Dockerfile:27
- Problem: `COPY pyproject.toml uv.lock` (line 21), then `uv pip install --system --no-cache-dir .`, which resolves from pyproject.toml and does not read uv.lock. With `[tool.uv] pip = { upgrade = true }` (pyproject.toml:29-30), every build picks the newest transitive versions (kombu, redis, billiard, urllib3 ...). Prod never runs what the lock and Dependabot pinned.
- Proposal: `RUN uv export --frozen --no-dev --no-emit-project -o /tmp/req.txt && uv pip install --system --no-cache-dir -r /tmp/req.txt && uv pip install --system --no-deps .`. Use `COPY --from=ghcr.io/astral-sh/uv:<ver> /uv /bin/uv` instead of `pip install uv` (line 26). Delete the `[tool.uv] pip` table.
- Risk: the first build after the change may pin older transitive versions than today's image. That is intended.

## 8. wait-for-db.sh + psql client + sleep 45 instead of compose healthchecks
- Severity: low | Category: ops | Effort: M
- File: infra/Dockerfile:17
- Problem: the image installs `gcc libpq-dev` (not needed: `psycopg2-binary` ships wheels) and `postgresql-client` only so django/entrypoints/wait-for-db.sh can poll with psql. `chmod +x` (Dockerfile:30) does nothing, because compose runs it as `sh script` (prod.yml:42, dev.yml:31). The worker waits for migrations with a fixed `sleep ${WORKER_START_DELAY_SECONDS:-45}` (prod.yml:87, dev.yml:69).
- Proposal: add `healthcheck: test: pg_isready -U $$POSTGRES_USER` on `db`, and `depends_on: db: {condition: service_healthy}` on web/worker/beat. Delete the apt line, the chmod, the entrypoint script and `entrypoint:`. Give web a healthcheck, or use `condition: service_started` plus Celery's own broker/DB retry, to replace the sleep.
- Risk: medium. It changes startup ordering in prod, so test it with `make dev-up` first.

## 9. Django CI workflow cruft
- Severity: low | Category: ci | Effort: S
- File: .github/workflows/django.yml:39
- Problem: the "Create .env file" step (39-43) is redundant, because `make verify` passes SECRET_KEY, DJANGO_DEBUG and ALLOWED_HOSTS inline (Makefile:36-38). It has a single-value matrix with `max-parallel: 4` (12-15), `master` branches that do not exist on the remote (5, 7), outdated `checkout@v3`/`setup-python@v4`, and `pip install uv` instead of `astral-sh/setup-uv`. Node is 20 in CI but 22 in the Dockerfile (Dockerfile:2).
- Proposal: drop the .env step, the matrix and `master`. Use `actions/checkout@v4` + `astral-sh/setup-uv` (python from `requires-python`). Align Node to 22.
- Risk: none.

## 10. Build/deploy workflow duplication and dead IMAGE_NAME
- Severity: low | Category: ci | Effort: S
- File: .github/workflows/docker-build-push.yml:16
- Problem: the job `env:` (16-25) duplicates the .env heredoc (47-66). `IMAGE_NAME` is set 3x (10, 52, 105) and in .env.example:30, but compose hardcodes `ghcr.io/stokuj/my-django-portfolio:latest` (prod.yml:37, 80, 120), so nothing reads it. The "Build CSS (preflight)" step (34-43) repeats the Dockerfile `css-builder` stage. `master` fallbacks in the deploy script (86, 100-101) refer to a branch that does not exist.
- Proposal: delete the job env, the IMAGE_NAME lines, the preflight CSS step and the master fallbacks. Optionally gate deploy on CI with `workflow_run` or a `needs:` test job.
- Risk: low. Compose interpolation only needs the .env file.

## 11. Unused npm devDependency
- Severity: low | Category: library | Effort: S
- File: package.json:13
- Problem: `@catppuccin/daisyui` is not referenced anywhere (input.css uses only `daisyui` and `daisyui/theme`).
- Proposal: `npm uninstall @catppuccin/daisyui`.
- Risk: none.

## 12. Transitive packages pinned as direct deps
- Severity: low | Category: library | Effort: S
- File: pyproject.toml:7
- Problem: `asgiref`, `packaging`, `pyjwt`, `sqlparse`, `tzdata` (lines 7, 14, 18, 20, 21) are never imported by the app (`uv tree --invert` shows they come via django/gunicorn/celery/redis). They were pinned as CVE floors, and they now look like real dependencies.
- Proposal: move them to `[tool.uv] constraint-dependencies = ["pyjwt>=2.12.0", ...]`, or drop them and rely on uv.lock once item 7 is applied.
- Risk: if dropped without item 7, the image may resolve older vulnerable versions. Keep them as constraints.

## 13. Redundant explicit bridge network
- Severity: low | Category: simplification | Effort: S
- File: infra/docker-compose.prod.yml:180
- Problem: `networks: app-network: driver: bridge`, plus `networks: [app-network]` on every service (both files), recreates the compose default network.
- Proposal: delete all `networks:` keys (about 15 lines per file).
- Risk: the network name changes, so the stack is recreated once on deploy (already done by `down`/`up`).

## 14. Prod Postgres published on host
- Severity: low | Category: ops | Effort: S
- File: infra/docker-compose.prod.yml:10
- Problem: prod `db` publishes `127.0.0.1:15432:5432`. Services reach it over the compose network, and this port is a copy of the dev setting.
- Proposal: remove `ports:` from prod db. Use `docker compose exec db psql` for manual access.
- Risk: breaks any SSH tunnel workflow that uses the port.

## 15. Caddyfile duplicate file_server blocks
- Severity: low | Category: simplification | Effort: S
- File: infra/Caddyfile:18
- Problem: identical `handle /static/*` and `handle /media/*` blocks (18-26), with inconsistent 1-space indent.
- Proposal: `@files path /static/* /media/*` + `handle @files { root * /srv; file_server }`.
- Risk: none.

## 16. .gitignore is the full GitHub Python template
- Severity: low | Category: simplification | Effort: S
- File: .gitignore:34
- Problem: 180 lines covering PyInstaller, Flask, Scrapy, Sphinx, PyBuilder, pdm, SageMath, Spyder and so on. Most of it is irrelevant to this repo.
- Proposal: cut it to about 20 relevant lines (venv, __pycache__, .env, media/, staticfiles/, node_modules/, style.css if generated, celerybeat-schedule, .coverage, editor dirs).
- Risk: low. Check `git status --ignored` before and after.

## 17. Doc drift in CLAUDE.md / implementation.md
- Severity: low | Category: docs | Effort: S
- File: CLAUDE.md:93
- Problem: CLAUDE.md names the CI workflow `django-ci.yml`, but the file is `.github/workflows/django.yml`. CLAUDE.md:29 uses pytest, which is not installed (see item 2). docs/implementation.md:106 still carries a transitional "new development workflow ... earlier versions" note.
- Proposal: fix the names and commands, and drop the transitional sentence.
- Risk: none.

## 18. `compileall` in verify is redundant
- Severity: low | Category: simplification | Effort: S
- File: Makefile:35
- Problem: `manage.py check` and the full test run already import every module that matters, and `compileall` also writes .pyc files into the tree.
- Proposal: delete the line.
- Risk: a syntax error in a module nothing imports would go unnoticed. ruff on `django/` would catch it if desired.

net: about -4.9k lines (about -4.4k docs, about -450 infra/tests/config), -1 npm dep, -5 direct Python pins, -3 apt packages possible.

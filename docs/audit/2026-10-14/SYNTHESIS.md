# Audit synthesis (2026-10-14, branch `dev`)

132 merged findings (F-001..F-107 from 20 lenses, F-108..F-132 from 4 gap passes). After verification: **129 confirmed, 3 refuted**.
Severity after verification: 0 critical, 3 high, 23 medium, 103 low.

Each row: severity as adjusted by the verifiers, location, the problem in one line, the chosen fix (the smallest correct one from the verifier alternatives), and effort (S < 30 min, M < half day, L more).
Execution order and branches are in `docs/audit/2026-10-14/PLAN.md` (owner decisions: `DECISIONS.md`).

## Top 5

1. **F-002** (high, tests): `make verify`/CI runs 26 operational tests and none of the 96 Django app tests.
2. **F-008** (high, ops): prod `web` and `caddy` have no restart policy, so the site stays down after a reboot or crash.
3. **F-004** (high, bug): the mobile menu likely never opens on iOS Safari.
4. **F-005** (medium, security): the public heatmap endpoint calls GitHub inline on every request while upstream is failing (DoS, burns the token's rate limit).
5. **F-109** (medium, security): `/admin/login/` has no brute-force limit, and each attempt costs PBKDF2 CPU on the single worker.

## Security (21)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-005 | medium | django/main/views.py:157 | The anonymous heatmap view fetches GitHub inline when the snapshot is stale or empty. Errors do not advance `fetched_at`, so every request refetches. | Serve the snapshot as is. Return 503 only when there is no payload. When stale or missing, `if cache.add('heatmap-refresh-lock',1,300): refresh_portfolio_heatmap_cache_task.delay()` (in try/except). Tests: 5 stale GETs give 0 fetches and at most 1 enqueue; no payload gives 503. Update test_views.py:241,281 and add `cache.clear()` in setUp. | S |
| F-109 | medium | django/config/urls.py:24 | `/admin/login/` allows unlimited guessing, and the PBKDF2 cost per attempt is a CPU DoS on 1 sync worker. | Put Caddy `basic_auth /admin* { {$ADMIN_BASIC_USER} {$ADMIN_BASIC_HASH} }` before reverse_proxy. Add the vars to .env.example and the caddy env. No new dependency. | S |
| F-021 | medium | django/config/settings.py:35 | A placeholder SECRET_KEY or DEBUG=True is never caught; `check --deploy` never runs. | In the deploy script, after `pull` and before `down`: `docker compose ... run --rm --no-deps --entrypoint "" web python manage.py check --deploy --fail-level WARNING`. The owner runs it once by hand first. Decide together with F-060 (W021). | S |
| F-017 | medium | .github/workflows/docker-build-push.yml:89 | The SSH deploy does not verify the host key. | Add `fingerprint: ${{ secrets.SERVER_SSH_FINGERPRINT }}`, with the value from `ssh-keygen -lf` run on the droplet. | S |
| F-018 | medium | .github/workflows/docker-build-push.yml:90 | appleboy/ssh-action, which holds the SSH key and PAT, is pinned to an old mutable tag. | Pin it to a full commit SHA with a `# vX.Y.Z` comment. If script_stop goes away, add `set -e`. Dependabot bumps the pins (F-054). | S |
| F-035 | medium | django/main/templates/projects/detail.html:52 | MathJax loads from `mathjax@3` (floating) with no SRI, and the site has no CSP. | Pin `mathjax@3.2.2` with `integrity` and `crossorigin="anonymous"`, and update test_views.py:493. Track CSP (report-only) separately. | S |
| F-011 | medium | pyproject.toml:10 | Django 5.1 is EOL with unpatched advisories. | Pin the latest Django 5.2.x LTS and run `uv lock`. **Blocked by F-007** (5.2 needs PG >= 14). | S |
| F-012 | low | .github/workflows/django.yml:9 | No `permissions` block, so GITHUB_TOKEN gets the repo default. | Add top-level `permissions: {contents: read}` in django.yml and top-level `permissions: {}` in docker-build-push.yml. build-and-push keeps its own override. | S |
| F-027 | low | django/main/static/js/mathjax-config.js:1 | MathJax runs without `ui/safe`, so `\href{javascript:}` passes. | Add `loader: {load: ['ui/safe']}`. | S |
| F-090 | low | django/main/views.py:64 | Any `class` value is allowed on div/span, so a README can overlay the page. | In `_clean_attributes`, `if name == "class": return value == "arithmatex"`, plus one test. | S |
| F-056 | low | .github/workflows/docker-build-push.yml:103 | A long-lived GHCR PAT is interpolated into the remote script. | Give the deploy job `permissions: {contents: read, packages: read}` and log in with `GITHUB_TOKEN`/`github.actor`. The owner then deletes the GHCR_PAT secret. | S |
| F-044 | low | infra/Caddyfile:18 | Caddy-served /static and /media get no security headers. | Add `header X-Content-Type-Options nosniff` on both. On /media add `Content-Security-Policy "default-src 'none'; sandbox"`. | S |
| F-108 | low | django/config/settings.py:179 | There is no cap on upload body size, and the settings comment is wrong. | Add `request_body { max_size 10MB }` to the Caddy app block and fix the comment. | S |
| F-046 | low | infra/Dockerfile:33 | The runtime user owns the app code. | Run chown only on staticfiles, media, celerybeat-schedule and /home/app. | S |
| F-102 | low | infra/Dockerfile:16 | gcc and libpq-dev ship in the runtime image. | Install only `postgresql-client`, and drop it after F-048. | S |
| F-103 | low | infra/docker-compose.prod.yml:10 | Prod Postgres is published on loopback port 15432. | Delete the `ports` lines (first confirm the owner has no tunnel workflow that uses them). | S |
| F-104 | low | infra/docker-compose.prod.yml:180 | The explicit bridge network is redundant and flat. | Delete the `networks` keys. | S |
| F-060 | low | django/config/settings.py:102 | HSTS `preload` and `includeSubDomains` are hardcoded for one year. | Read them with `env.bool(..., default=False)`. Decide together with F-021, because `--fail-level WARNING` fails on W021. | S |
| F-118 | low | django/main/admin.py:63 | The TaskExecutionStatus and TaskExecutionLog admins allow add and change. | Return False from `has_add_permission` and `has_change_permission`, and keep delete. | S |
| F-052 | low | pyproject.toml:15 | Pillow 12.2.0 has advisories (admin-only path). | Pin `pillow==12.3.0` and run `uv lock --upgrade-package pillow`. | S |
| F-101 | low | infra/Dockerfile:2 | Base image tags float, and the app ships only as `:latest`. | Fold into F-001 (SHA tag) and F-054 (Dependabot docker). Pin digests only once Dependabot is in place. | S |

## Ops (12)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-008 | high | infra/docker-compose.prod.yml:33 | `web` and `caddy` have no restart policy. | Add `restart: always` to both. | S |
| F-001 | medium | .github/workflows/docker-build-push.yml:107 | Deploy runs `down` then `--force-recreate` (full downtime), has no concurrency guard, and its prune removes the rollback image. | Add a workflow `concurrency: {group: deploy-prod, cancel-in-progress: false}` and replace :108-109 with `up -d --remove-orphans --wait`. Update tests/test_operational_files.py:79-95. Optional: push `:${{ github.sha }}`, use `image: ...:${IMAGE_TAG:-latest}`, and `git checkout ${{ github.sha }}` on the server. | S-M |
| F-007 | medium | infra/docker-compose.prod.yml:3 | postgres:13 is EOL, and it blocks Django 5.2. | **Plan only.** Owner-run dump/restore to postgres:17 on a new **external** volume, keeping `postgres_data` for rollback (runbook in the plan, Phase 3j). | M |
| F-009 | medium | infra/docker-compose.prod.yml:46 | Gunicorn runs on defaults: 1 sync worker and no access log. | `--workers 2 --threads 4 --access-logfile -`. Size to `free -m`. Keep the 30s timeout once F-005 is done. | S |
| F-010 | medium | infra/docker-compose.prod.yml:185 | There are no backups of the database or media. | Owner enables DigitalOcean droplet backups. Optionally add a pre-deploy `pg_dump -Fc` to `~/backups` with 14-day retention, plus a restore note. | S |
| F-024 | medium | django/main/middleware.py:15 | Every cookieless home hit creates a session row that is never purged. | Store the visitor flag in a plain `has_visited` cookie (httponly, Lax, SESSION_COOKIE_AGE) instead of the session. Run `clearsessions` once by hand. | S |
| F-032 | medium | django/main/tasks.py:202 | The disk check runs daily and alerts nobody. | Owner sets a DO Monitoring alert (disk > 85%, email). No code change. | S |
| F-048 | low | infra/docker-compose.prod.yml:87 | No healthchecks; startup relies on `sleep 45` and a wait-for-db loop that never ends. | Add a `pg_isready` healthcheck on db in both compose files and `db: {condition: service_healthy}`. Delete the entrypoint, wait-for-db.sh, the chmod and postgresql-client. | S |
| F-062 | low | django/config/settings.py:214 | No Celery task time limit. | `CELERY_TASK_TIME_LIMIT = 600`, `CELERY_TASK_SOFT_TIME_LIMIT = 540`. | S |
| F-078 | low | django/main/tasks.py:260 | TaskExecutionLog grows without bound. | After the create, delete rows with `created_at` older than 90 days. | S |
| F-015 | low | .github/workflows/docker-build-push.yml:80 | `workflow_dispatch` from any branch overwrites `:latest`. | Add `if: github.ref == 'refs/heads/main'` on build-and-push. | S |
| F-132 | low | infra/Caddyfile:29 | No robots.txt, so crawler hits render a DB-backed 404. | Caddy `respond /robots.txt "User-agent: *\nDisallow: /admin/\n" 200`. | S |

## Tests (11)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-002 | high | Makefile:38 | Label-less `manage.py test` from the repo root finds only tests/ (26 of 122 tests). | `SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 DB_ENGINE=django.db.backends.sqlite3 uv run python django/manage.py test main tests`. | S |
| F-038 | medium | django/main/tests/test_views.py:77 | The "heatmap disabled" tests always pass, read .env, and hit the real GitHub API. | Put `@override_settings(GITHUB_HEATMAP_TOKEN="")` on ViewsTest and URLsTest, assert `context['heatmap_enabled']`, and assert exactly 404. | S |
| F-031 | low | django/main/tasks.py:145 | Task failure branches are untested. | Test sync raises -> PARTIAL/FAILURE with `task_exception`, and heatmap fetch returns `(None,'x')` -> FAILURE plus a log row. | S |
| F-037 | low | django/main/tests/test_markdown_sync.py:15 | The download guards are untested. | Delete the dead Content-Length block (with F-070). Test 404 then fallback, and rejection of an HTML body. | S |
| F-039 | low | django/main/tests/test_views.py:632 | The disk-threshold fix has no regression test, and the test reads the real disk. | Patch `main.views.shutil.disk_usage`: 0.96 GB gives critical, 1.96 GB gives warning. | S |
| F-042 | low | django/main/views.py:357 | No negative tests for the sanitizer. | One SimpleTestCase with subTest over: a `javascript:` link, onclick/style, iframe, and a look-alike host img. | S |
| F-053 | low | tests/test_operational_files.py:51 | String-grep change-detector tests. | Trim to the #55/#57 checks. Add `docker compose -f infra/docker-compose.prod.yml config -q` to CI (on the runner, after `cp .env.example .env`). | S |
| F-066 | low | django/main/github_client.py:57 | The GitHub error mapping is partly untested. | Turn the 401 test into a subTest over 401/403/500, and test the upstream-error message. Adapt if F-023 lands. | S |
| F-087 | low | django/main/tests/test_models.py:289 | markdown_file cleanup and camo/github.com images are untested. | Copy the 2 thumbnail tests for markdown_file, and extend test_views.py:622 with camo and github.com images. | S |
| F-088 | low | django/main/tests/test_views.py:58 | Legacy negative asserts and `!= 302` checks. | Drop the assertNotContains on removed UI, rename `test_task_3_*`, and assert exact status codes. | S |
| F-097 | low | django/main/views.py:422 | Staff endpoint error branches are untested. | Test that `delay` raising gives a 302 and an error message, for both views. | S |

## Bug (16)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-004 | high | django/main/templates/base.html:25 | The menu JS only removes `hidden`, but daisyUI needs `.dropdown-open` or focus, so the menu likely never opens on iOS. | In mobile-menu.js:10 toggle `dropdown-open` on the `.dropdown` wrapper, drop `hidden` at base.html:42, and return early from Escape unless open. Verify in WebKit or on an iPhone. | S |
| F-003 | medium | django/main/markdown_sync.py:168 | Each sync rewrites the file and the name grows (`slug_X_Y.md`). | Skip the write when the content is unchanged (count it as success). Otherwise overwrite in place with `storage.open(name,'wb')`, and `save()` only when no file exists. Test that the name is stable. | S |
| F-029 | medium | django/main/static/src/css/input.css:9 | Unlayered h1-h3 rules override every Tailwind size. | Wrap :9-17 in `@layer base {}`. | S |
| F-034 | medium | django/main/templates/pages/about.html:3 | Pages override the nonexistent `page_name` block, so every title is "My Portfolio". | Rename it to `title` in about.html:3 and detail.html:4 (with F-111). | S |
| F-040 | medium | django/main/views.py:95 | The 500 handler runs DB context processors, so a DB outage gives a bare error page. | Move the errors templates to the templates root and delete the handlers (views.py:90-97, config/urls.py:32-34). Rewrite ErrorHandlersTest. | S |
| F-025 | low | django/main/models.py:47 | A case-only duplicate tag gives a 500 in the admin. | Add `clean()` that uppercases the name. | S |
| F-026 | low | django/main/models.py:238 | The media file is deleted even when the transaction rolls back. | Delete through `transaction.on_commit` in `_delete_file_field`. Tests use `captureOnCommitCallbacks(execute=True)`. | S |
| F-059 | low | django/config/settings.py:43 | Host and origin list entries are not stripped. | `[h.strip() for h in env.list(...) if h.strip()]` at :43 and :107. | S |
| F-067 | low | django/main/github_client.py:60 | A rate-limit 403 is reported as an invalid token. | For a 403 with `X-RateLimit-Remaining == '0'` or `Retry-After`, raise GitHubUpstreamError. Add one test. | S |
| F-073 | low | django/main/static/js/mathjax-config.js:3 | `$` delimiters typeset dollar amounts. | Use the Arithmatex generic config: `\(..\)`/`\[..\]` only, `ignoreHtmlClass: '.*\|'`, `processHtmlClass: 'arithmatex'`. | S |
| F-076 | low | django/main/tasks.py:36 | A single-slug or empty run overwrites the global status with SUCCESS. | Remove the unused `blog_slug` parameter (tasks.py:30,37-38; views.py:426-437) and update test_views.py:551. | S |
| F-077 | low | django/main/tasks.py:74 | `last_success_at` is cleared on every failure. | Delete the 6 `last_success_at=None` and the 3 `last_failure_at=None` lines, and update test_tasks.py:189,231,331. | S |
| F-079 | low | django/main/templates/base.html:54 | Both menus show between 768 and 1023px. | Change `lg:hidden` to `md:hidden` at base.html:25. | S |
| F-089 | low | django/main/urls.py:5 | The URL name `home` is duplicated, so reverse gives /home/. | Make `home/` a `RedirectView(pattern_name="home", permanent=True)` with no name. Update the tests and the middleware.py:13 tuple. | S |
| F-120 | low | django/main/models.py:60 | A markdown upload is checked only by extension, and the sync silently replaces it. | Add a UTF-8 decode validator and help_text (a no-op AlterField migration). | S |
| F-128 | low | django/main/templates/projects/components/blog_sidebar_cards.html:6 | A JSON string renders one badge per character. | Add a `validate_str_list` validator on both JSON fields and one full_clean test. | S |

## CI (6)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-016 | medium | .github/workflows/docker-build-push.yml:84 | Build and deploy are not gated on tests. | Add `workflow_call:` to django.yml, then `verify: uses: ./.github/workflows/django.yml` and `needs: verify` on build-and-push. | S |
| F-020 | medium | Makefile:39 | Ruff skips django/ (31 violations). | Add `extend-exclude = ["django/main/migrations"]` and use `uv run ruff check .`. Run `--fix` in its own commit, then fix E501/F841 by hand. | S |
| F-013 | low | .github/workflows/django.yml:18 | Deprecated actions, a one-entry matrix, master triggers and unlocked `uv sync`. | Drop the matrix and master, move to Node-24 action majors (or pinned setup-uv), use `uv sync --locked --extra dev`, and drop the .env step. | S |
| F-014 | low | .github/workflows/django.yml:22 | CI builds CSS on EOL Node 20, while the image uses Node 22. | Set node-version 22 in django.yml. Delete the preflight CSS and setup-node steps in docker-build-push.yml:34-42. | S |
| F-054 | low | .github/dependabot.yml:1 | No Dependabot config. | Weekly `github-actions` (`/`) and `docker` (`/infra`). | S |
| F-055 | low | .github/workflows/docker-build-push.yml:16 | Duplicated job env, a dead IMAGE_NAME and master fallbacks. | Delete the job env, the IMAGE_NAME lines and the master refs. Keep the .env heredoc. | S |

## Library (6)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-045 | medium | infra/Dockerfile:27 | The image ignores uv.lock, so transitive dependencies float on every build. | `COPY --from=ghcr.io/astral-sh/uv:<pin> /uv /bin/uv`, then `uv export --frozen --no-dev --no-emit-project -o /tmp/req.txt`, `uv pip install --system -r`, and `--no-deps .`. Delete the `[tool.uv] pip` table. | S |
| F-050 | medium | pyproject.toml:7 | Transitive packages are pinned directly, some of them vulnerable. | Remove asgiref, packaging and tzdata. Use `pyjwt>=2.15.0` and `sqlparse>=0.6.0`, then `uv lock`. | S |
| F-051 | low | pyproject.toml:9 | Celery 5.4 is not officially supported on Python 3.13. | `celery[redis]==5.6.3`, `uv lock`, then a worker and beat smoke test. | S |
| F-106 | low | pyproject.toml:11 | Routine bumps are available. | PR A: django-environ, markdown, requests, ruff, `npm update`. PR B: gunicorn 26 and pymdown-extensions 12, after reading their changelogs. | S |
| F-107 | low | pyproject.toml:16 | psycopg2-binary instead of psycopg 3. | `psycopg[binary]`, with the version checked on PyPI when making the change, then a smoke test on Postgres. | S |
| F-105 | low | package.json:13 | @catppuccin/daisyui is unused. | `npm uninstall @catppuccin/daisyui`, then `npm run build:css:prod`. | S |

## Simplification (18)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-030 | low | django/main/tasks.py:119 | Status bookkeeping is copy-pasted 5 times, and there is a redundant no-token branch. | Add a `_finish(status, state, total, updated, error="")` helper and delete :119-143. Tests use `override_settings(GITHUB_HEATMAP_TOKEN="")`. | S |
| F-033 | low | django/main/tasks.py:250 | The self-rescheduling path is dead. | Delete `schedule_next`, `_maybe_schedule_next_refresh`, `_schedule_next_heatmap_refresh`, the beat kwargs and the apply_async mock. | S |
| F-023 | low | django/main/github_client.py:49 | Two HTTP calls and 7 isinstance checks. | Use one GraphQL `viewer { login contributionsCollection ... }` query with a single try/except (KeyError, TypeError). Delete `fetch_authenticated_user`. | M |
| F-068 | low | django/main/heatmap.py:68 | Unused override parameters and settings that are re-defaulted. | Delete the parameters. `get_configured_github_token` becomes `return settings.GITHUB_HEATMAP_TOKEN or None`. | S |
| F-070 | low | django/main/markdown_sync.py:105 | Redundant except clauses, a dead Content-Length check and a hand-written dedup. | Drop the try/except around get and lines :112-121, use `list(dict.fromkeys(...))`, and catch `(OSError, ValueError)`. | S |
| F-061 | low | django/config/settings.py:181 | Dead or default settings, plus Polish comments. | Delete STATICFILES_STORAGE, `Env(DEBUG=...)`, CELERY_RESULT_BACKEND (plus the compose and .env.example lines), one DEFAULT_AUTO_FIELD and the commented prints. Translate the comments. | S |
| F-049 | low | infra/scripts/compose_status.py:1 | Python helpers duplicate `docker ps` and copy-if-missing. | Use Makefile one-liners. Delete infra/scripts/, test_operational_helpers.py and test_operational_files.py:34-37. | S |
| F-047 | low | infra/docker-compose.prod.yml:52 | Environment blocks are repeated 6 times. | Delete the 4 lines that env_file already supplies from each of the 6 blocks (-24 lines). Skip anchors. | S |
| F-091 | low | django/main/views.py:103 | The timeline duplicates STATUS_CHOICES. | Iterate `Project.STATUS_CHOICES`. | S |
| F-092 | low | django/main/views.py:200 | A 38-line defensive re-parse of our own payload. | Replace it with a one-line `sum(...)` with both date bounds. | S |
| F-093 | low | django/main/views.py:240 | The disk classification is implemented twice. | Add `disk_level(free_gb)` in tasks.py and use it in both places. | S |
| F-094 | low | django/main/views.py:340 | Dead context keys and classes, and manual file handling. | Delete them, and use `with ...open('rb') as f: f.read().decode('utf-8-sig')`. | S |
| F-065 | low | django/main/context_processors.py:28 | The active-profile lookup appears 3 times. | Add a `PortfolioProfile.get_active()` classmethod. Skip un-flattening the processor. | S |
| F-084 | low | django/main/templates/pages/about.html:260 | The heatmap JS is over-generalised. | Keep it inline. Use direct consts, delete the daisy branch and the `contribution_count` fallback, and colour cells with `COLORS[day.level\|\|0]`. | S-M |
| F-086 | low | django/main/templates/projects/components/project_card.html:9 | Duplicated img blocks. | Merge them into one `<img>`. The status-badge include is optional. | S |
| F-081 | low | django/main/templates/base.html:165 | Dead CSS classes. | Delete `hover:bg-primary-focus`, `menu-compact` and `not-prose`. Keep `prose`. | S |
| F-100 | low | infra/Caddyfile:18 | Duplicate file_server blocks. | `@files path /static/* /media/*` with one `handle @files`. Scope the F-044 media CSP with `header /media/* ...`. | S |
| F-057 | low | .gitignore:34 | The .gitignore is the full GitHub Python template. | Cut it to about 20 relevant lines and diff `git status --ignored --porcelain` before and after. | S |

## Architecture (4)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-041 | low | django/main/views.py:264 | The jobs panel hardcodes the schedule, computes the wrong next run and omits the disk task. | Iterate `CELERY_BEAT_SCHEDULE` with one label dict. Next run is `now + entry['schedule'].remaining_estimate(now)`. Map `main.tasks.X` to `main.X`. | S |
| F-072 | low | django/main/models.py:118 | TaskExecutionStatus duplicates the latest log row. | Drop the model (migration) and read the latest log per task. | M |
| F-069 | low | django/main/markdown_sync.py:13 | Hardcoded BLOG_REPO_PATHS duplicates `github_url`. | The owner backfills `github_url` in prod first. Then delete the dict and its fallbacks, and the footer uses `project.github_url`. | M |
| F-119 | low | django/main/admin.py:116 | The PageView singleton is registered raw. | A ModelAdmin with add and delete disabled, and `count` read-only. | S |

## Performance (6)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-099 | low | infra/Caddyfile:16 | Static files are served uncompressed and with no caching. | Add `encode zstd gzip` first. Later, ManifestStaticFilesStorage (run collectstatic in verify) and then immutable Cache-Control for /static only. | S-M |
| F-082 | low | django/main/templates/components/hero_section.html:2 | The hero PNGs total 4.3 MB, and one is unused. | Delete hero-bg3.png, re-encode the other two to WebP at q70 and update the includes. | S |
| F-022 | low | django/config/settings.py:109 | No persistent DB connections. | `"CONN_MAX_AGE": 60, "CONN_HEALTH_CHECKS": True`. | S |
| F-096 | low | django/main/views.py:402 | The sidebar query loads every column. | `.only("id","title","blog","blog_url","github_url","date")`. Skip the HTML cache. | S |
| F-064 | low | django/main/context_processors.py:10 | 3 uncached queries per render. | Optional: cache only the profile (LocMem, 300s) with save/delete signal invalidation. | S |
| F-071 | low | django/main/middleware.py:10 | Redundant SELECT before UPDATE. | Won't fix unless the file is already being edited. | S |

## Frontend (18)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-111 | low | django/main/templates/base.html:8 | The default title ignores `site_name`, and the index page has no title. | `{% block title %}{{ site_name\|default:"My Portfolio" }}{% endblock %}`, and `Projects \| ...` on the index (with F-034). | S |
| F-028 | low | django/main/static/js/theme-toggle.js:32 | Dark theme flashes light first, localStorage calls are unguarded, and legacy migration code remains. | An inline head script sets the saved theme (in try/catch). Wrap storage calls in try/catch and delete `legacyThemeMap`. OS preference support is optional. | S |
| F-036 | low | django/main/templates/projects/index.html:40 | The server-rendered grid is hidden behind a fake skeleton until JS runs. | Delete the skeleton and `hidden`, plus projects-filters.js:8, 89-90 and the guard on :11. | S |
| F-110 | low | django/main/templates/base.html:5 | No meta description. | A `meta_description` block, overridden in about and detail. | S |
| F-121 | low | django/main/templates/base.html:5 | No Open Graph or Twitter tags. | og:title, og:description, og:url and an absolute og:image, plus twitter:card. | S |
| F-122 | low | django/main/templates/base.html:5 | No favicon, so /favicon.ico gives a Django 404. | Add favicon.svg with a link tag, and Caddy `redir /favicon.ico /static/images/favicon.svg`. | S |
| F-085 | low | django/main/templates/pages/about.html:421 | The heatmap is not accessible. | The grid gets `role="img"` and a summary label. Drop the per-cell aria-label and add `role="alert"` on the error box. | S |
| F-083 | low | django/main/templates/components/timeline_section.html:2 | The accordion uses unlabelled radios. | `<details name="timeline-accordion">` with a `<summary>`. | S |
| F-075 | low | django/main/static/js/projects-filters.js:76 | Tag filter state is shown by colour only. | Set `aria-pressed` in the template and in the loop. | S |
| F-080 | low | django/main/templates/base.html:152 | Nav and footer semantics are missing. | `aria-current` via resolver_match, `aria-hidden` on the SVG, and delete the duplicate footer link. | S |
| F-127 | low | django/main/templates/projects/components/blog_projects_sidebar.html:8 | The sidebar marks the current project with CSS only. | `aria-current="page"` on the active link. | S |
| F-124 | low | django/main/templates/components/hero/about_content.html:8 | `#` fallback links are dead. | Return `''` from the context processor and guard the links with `{% if %}` (including project_footer.html:6). | S |
| F-126 | low | django/main/templates/components/timeline_project_item.html:13 | A duplicate "Learn More" link to GitHub. | Delete the `{% elif project.github_url %}` branch. | S |
| F-123 | low | django/main/templates/base.html:63 | Social links are inconsistent between header and footer. | Add `target="_blank" rel="noopener noreferrer"` to the header links. | S |
| F-125 | low | django/main/templates/components/timeline_project_item.html:2 | `<time>` has no machine-readable value. | `datetime="{{ project.date\|date:'Y-m' }}"`. | S |
| F-074 | low | django/main/static/js/projects-filters.js:16 | The debounce is unnecessary. | Call `applyFilters` directly. Keep the clear button. | S |
| F-117 | low | django/main/admin.py:14 | The admin list views are hard to use. | Trim list_display, and add list_filter and filter_horizontal. For logs, add list_filter and date_hierarchy. | S |
| F-116 | low | django/config/settings.py:47 | No sitemap. | Only if search indexing is a goal: contrib.sitemaps for blog projects and static pages. | S |

## Docs (11)

| ID | Sev | Location | Problem | Chosen fix | Eff |
|----|-----|----------|---------|------------|-----|
| F-019 | medium | CLAUDE.md:93 | CLAUDE.md names the wrong workflow, a pytest command and the wrong verify scope. | :23 `manage.py test main` (with the env vars). :29 `uv run python -m unittest discover -s tests -t .`. :34 `ruff check .`. :93 `django.yml` on push/PR to main. | S |
| F-115 | low | README.md:143 | The `make verify` prerequisites omit npm. | "expects `uv sync --extra dev` and `npm install`". | S |
| F-098 | low | docs/implementation.md:36 | healthcheck_task is documented but unused, and the disk task is undocumented. | Delete healthcheck_task, its test and its doc line. Document the disk task in implementation.md, architecture.md and CLAUDE.md. | S |
| F-130 | low | docs/architecture.md:146 | Periodic jobs are listed incompletely. | List all 3 beat entries with their schedules. | S |
| F-043 | low | docs/superpowers/plans/2026-05-14-codebase-audit.md:1 | Obsolete or diverging 2026-05 specs and plans. | `git rm` the 2026-05-* plans and specs (git keeps them; this plan stays). | S |
| F-063 | low | django/config/settings.py:220 | The beat key says hourly but the job runs every 2h. | Rename it to `sync-project-markdowns-every-2h`. | S |
| F-112 | low | .env.example:30 | IMAGE_NAME is unused. | Delete the line. | S |
| F-113 | low | README.md:67 | The About page is called the landing page. | Drop "The main landing page". | S |
| F-114 | low | README.md:106 | The Python prerequisite says "3.13+". | "Python 3.13". | S |
| F-129 | low | docs/architecture.md:6 | The service list describes prod only. | "In production (...)" plus one line on dev (no Caddy, runserver). | S |
| F-131 | low | docs/frontend.md:42 | The diagram misses edges and templates. | Add Errors -> Hero, both sidebar partials and a HeroContent node. | S |

## Refuted

- F-006: "bleach 6.2.0 has known sanitizer bypasses and is deprecated upstream"
- F-058: "compileall in verify is redundant"
- F-095: "Outbound README links get no rel=nofollow/noopener"

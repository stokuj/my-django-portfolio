# Plan: 2026-10-14 audit fixes and upgrades

**Decisions first.** `docs/audit/2026-10-14/DECISIONS.md` holds the owner's answers and overrides this plan where they differ. Read it before each phase.

**Source of truth.** Findings, problems and chosen fixes are in `docs/audit/2026-10-14/SYNTHESIS.md`. Evidence is in `docs/audit/2026-10-14/verify/F-xxx-*.md`.

## Rules for whoever executes this

- **Resume from this file.** In a new session, read this file, find the first phase that still has unticked `- [ ]` tasks, and continue there.
- **Tick and commit after each task.** Change `- [ ]` to `- [x]` in this file, in the same commit as the change. Use one commit per task, with an English, conventional message that names the F-id.
- **A phase starts when the owner writes "faza N".** Inside a phase, stop only on a red `make verify`, an error, or an [OWNER] step. At the end, report what changed and the verification output.
- **Never touch `.env`** (do not read, edit, copy or create it). `.env.example` may be edited where a task says so.
- Branches are created from `dev` (`git switch dev && git switch -c <branch>`). Do not push, merge, approve or open PRs unless the owner asks. Never touch `main`.
- **[OWNER]** tasks need the server, the DigitalOcean console or GitHub secrets. The agent prepares the instructions and does not execute them.
- **Production is off** (old droplet archived, a new one comes later). Server-side [OWNER] steps go into the "New droplet bootstrap" list in `docs/implementation.md` (it absorbed the first-deploy checklist in 3i), not into a wait. Do not open `dev → main` PRs until the new droplet exists.
- When a task changes compose files, the Makefile or workflows, update `tests/test_operational_files.py` in the same commit (its string-count tests break easily; see F-053).
- Priority note: the three high findings are F-002 (Phase 1), F-004 and F-008 (Phase 4). Each is S effort. F-004 and F-008 stay in Phase 4.

Baseline: `make verify` (after Phase 1 it runs both test suites).

---

## Phase 1: Fix verification

- **Goal:** `make verify` runs all 122 tests, ruff lints django/, docs describe what CI really does, and no deploy happens without verify.
- **Branch:** `chore/audit-p1-verify`
- **Files:** `Makefile`, `pyproject.toml` ([tool.ruff]), `django/main/tests/*` (ruff fixes, F-038), `tests/test_urls.py`, `.github/workflows/django.yml`, `.github/workflows/docker-build-push.yml`, `CLAUDE.md`, `README.md`
- **Verify:** `make verify`. Expect `Ran 122 tests ... OK` and ruff clean. Also `uv run ruff check .`.
- **Risk:** low. Tests that broke silently may now surface; fix them in this phase.

- [x] F-002: `Makefile:38` becomes `SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 DB_ENGINE=django.db.backends.sqlite3 uv run python django/manage.py test main tests`. Fix any app test that fails.
- [x] F-038: Put `@override_settings(GITHUB_HEATMAP_TOKEN="")` on ViewsTest and URLsTest, assert `response.context["heatmap_enabled"]`, and change `test_urls.py:35-37` to `assertEqual(status, 404)`. This stops tests reading .env or calling GitHub.
- [x] F-020: Add `extend-exclude = ["django/main/migrations"]` under `[tool.ruff]` and change `Makefile:39` to `uv run ruff check .`. Commit A: `ruff check . --fix`. Commit B: fix the E501 lines by hand, and check the unused `second` variables (test_tasks.py:98,200) before deleting them.
- [x] F-016: Add `workflow_call:` to the `on:` block of django.yml. In docker-build-push.yml add `verify: uses: ./.github/workflows/django.yml` and put `needs: verify` on build-and-push.
- [x] F-019: Update CLAUDE.md. :23 becomes `manage.py test main` with the env vars, :29 becomes `uv run python -m unittest discover -s tests -t .`, the Linting command becomes `uv run ruff check .`, and :93 says `django.yml` runs `make verify` on push/PR to main. Also remove the transitional sentence in docs/implementation.md:106.
- [x] F-115: Change `README.md:143` to "`make verify` expects `uv sync --extra dev` and `npm install` (it builds CSS first)."

**End of phase: report what changed and the verification output.**

---

## Phase 2: Security fixes

- **Goal:** close the confirmed security gaps that do not need a dependency upgrade.
- **Branch:** `fix/audit-p2-security`
- **Files:** `django/main/views.py`, `django/main/tests/test_views.py`, `django/config/settings.py`, `django/main/admin.py`, `django/main/static/js/mathjax-config.js`, `django/main/templates/projects/detail.html`, `infra/Caddyfile`, `infra/Dockerfile`, `infra/docker-compose.prod.yml`, `.github/workflows/*.yml`, `.env.example`, `tests/test_operational_files.py`
- **Verify:** `make verify`. Then `docker run --rm -e APP_DOMAIN=example.com -v $PWD/infra/Caddyfile:/etc/caddy/Caddyfile:ro caddy:2 caddy validate --config /etc/caddy/Caddyfile`, `docker build -f infra/Dockerfile .`, and `make dev-up` as a smoke test.
- **Risk:** medium. Caddy basic_auth and `check --deploy` can lock out the admin or block a deploy if the owner has not set the secrets and env first.

### Findings (approved in DECISIONS.md; F-060 and F-103 are skipped)

| ID | Sev | Issue | Fix | Owner action needed |
|----|-----|-------|-----|---------------------|
| F-005 | medium | Public heatmap endpoint fetches GitHub inline, with no backoff | Serve the snapshot. Enqueue a refresh behind `cache.add` lock. 503 only when there is no payload | none |
| F-109 | medium | /admin login can be brute-forced; PBKDF2 CPU DoS | Caddy `basic_auth /admin*` | first-deploy checklist |
| F-021 | medium | Placeholder SECRET_KEY/DEBUG never caught | `check --deploy --fail-level WARNING` in deploy before `down` | none (run locally) |
| F-060 | low | HSTS preload/includeSubDomains hardcoded | Skipped: HSTS stays as is (Q7) | none |
| F-017 | medium | No SSH host key verification | `fingerprint:` input | first-deploy checklist |
| F-056 | low | Long-lived GHCR PAT inlined | Log in with GITHUB_TOKEN + `packages: read` | first-deploy checklist |
| F-012 | low | No workflow `permissions` | `contents: read` / `{}` | none |
| F-015 | low | Dispatch from any branch overwrites `:latest` | `if: github.ref == 'refs/heads/main'` on build-and-push | none |
| F-035 | medium | MathJax floating version, no SRI | Pin 3.2.2 + integrity + crossorigin | none |
| F-027 / F-073 | low | No ui/safe; `$` typesets prices | Load `ui/safe`, keep only `\(..\)`/`\[..\]` delimiters, use `processHtmlClass: 'arithmatex'` | none |
| F-090 / F-042 | low | Any class allowed on div/span; sanitizer has no negative tests | Allow only `class="arithmatex"`; table-driven sanitizer test | none |
| F-044 | low | No nosniff on /static and /media | Caddy headers; CSP sandbox on /media | none |
| F-108 | low | No upload body cap | Caddy `request_body { max_size 10MB }`; fix settings comment | none |
| F-046 | low | Runtime user owns the code | chown only the writable dirs | none |
| F-102 | low | gcc/libpq-dev in runtime image | install only postgresql-client | none |
| F-103 | low | Prod Postgres on loopback 15432 | Skipped: owner uses an SSH tunnel (Q9) | none |
| F-104 | low | Redundant flat network | remove `networks` keys | none |
| F-118 | low | System-row admins allow add/change | view-only admins | none |
| F-011, F-018, F-050, F-052, F-101 | med/low | Outdated or vulnerable dependencies and actions | handled in Phase 3 | - |

### Tasks

- [x] F-005: In `about_heatmap_data`, never fetch inline. Serve the snapshot. If it is stale or has no payload, `if cache.add("heatmap-refresh-lock", 1, 300): try: refresh_portfolio_heatmap_cache_task.delay() except Exception: pass` (add a `# ponytail: per-process LocMem lock, use Redis cache if workers > 1 process` comment). Return 503 only when there is no payload. Tests: rewrite test_views.py:241 and :281; add "no payload gives 503 + enqueue" and "5 stale GETs give 0 fetches, 1 enqueue"; add `cache.clear()` in setUp.
- [x] F-109: In the Caddyfile apex block, before reverse_proxy, add `basic_auth /admin* { {$ADMIN_BASIC_USER} {$ADMIN_BASIC_HASH} }`. Add both vars to `.env.example` (with a comment pointing to `caddy hash-password`) and pass them to the caddy service env in prod compose. Add "set ADMIN_BASIC_USER/ADMIN_BASIC_HASH in the server .env" to the first-deploy checklist.
- [x] F-021: Leave the HSTS settings unchanged. In docker-build-push.yml, after `pull` and before `down`, add `docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml run --rm --no-deps --entrypoint "" web python manage.py check --deploy --fail-level WARNING`. Run `manage.py check --deploy --fail-level WARNING` locally with prod-like env (DEBUG off, a real-looking SECRET_KEY); it must pass with no silenced checks.
- [x] F-060: Skipped (Q7: HSTS stays as is).
- [x] F-017: Add `fingerprint: ${{ secrets.SERVER_SSH_FINGERPRINT }}` to the ssh-action `with:`. Add "add the SERVER_SSH_FINGERPRINT secret (SHA256 from `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the droplet)" to the first-deploy checklist.
- [x] F-056: Give the deploy job `permissions: {contents: read, packages: read}`. In the script, log in with `${{ secrets.GITHUB_TOKEN }}` / `${{ github.actor }}`. Add "delete the GHCR_PAT and GHCR_USERNAME secrets after the first successful deploy" to the first-deploy checklist.
- [x] F-012: Add top-level `permissions: {contents: read}` to django.yml and top-level `permissions: {}` to docker-build-push.yml. Job-level overrides stay.
- [x] F-015: Add `if: github.ref == 'refs/heads/main'` to build-and-push.
- [x] F-035: Pin `mathjax@3.2.2/es5/tex-mml-chtml.js` with `integrity="sha384-..."` and `crossorigin="anonymous"`, and update test_views.py:493.
- [x] F-027 + F-073: In mathjax-config.js add `loader: {load: ['ui/safe']}`, `tex: {inlineMath: [["\\(","\\)"]], displayMath: [["\\[","\\]"]], processEscapes: true, processEnvironments: true}`, and `options: {ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex"}`.
- [x] F-090: In `_clean_attributes` (views.py:77) add `if name == "class": return value == "arithmatex"`, plus a test that strips an overlay class.
- [x] F-042: Add a SimpleTestCase with subTest that calls `_render_markdown_to_html` on `[x](javascript:alert(1))`, `<a onclick=x style=y>`, `<iframe>`, and `<img src="https://github.com.evil.tld/a.png">`, and asserts the dangerous tokens are gone.
- [x] F-044: Caddy: add `header X-Content-Type-Options nosniff` for /static and /media, and `header /media/* Content-Security-Policy "default-src 'none'; sandbox"`. Check that thumbnails still render.
- [x] F-108: Add `request_body { max_size 10MB }` to the Caddy app block, and fix the comment at settings.py:179.
- [x] F-046: Dockerfile:33-36 chown applies only to `/app/staticfiles /app/media /app/django/celerybeat-schedule /home/app`. Check that collectstatic and beat start in `make dev-up`.
- [x] F-102: Dockerfile:17 becomes `apt-get install -y --no-install-recommends postgresql-client`.
- [x] F-103: Skipped (Q9: the owner uses an SSH tunnel to 127.0.0.1:15432).
- [x] F-104: Delete the top-level `networks` block and the per-service `networks` keys in prod compose.
- [x] F-118: Return False from `has_add_permission` and `has_change_permission` in the TaskExecutionStatus and TaskExecutionLog admins. Keep delete.

**End of phase: report what changed and the verification output.**

---

## Phase 3: Dependency upgrades (one branch/PR per upgrade)

- **Goal:** supported, patched and locked dependencies. Every sub-step is its own branch from `dev`, and each can be reverted on its own.
- **Verify (each step):** `uv lock --locked` (where the lock changed), `make verify`, `docker build -f infra/Dockerfile .`, and `make dev-up` as a smoke test (web, worker and beat start).
- **Risk:** medium overall. Django and PostgreSQL are the risky ones; the rest are low. Production is off, so nothing here touches live data.

### 3a. GitHub Actions majors and pinning (`chore/deps-actions`), risk low
Files: `.github/workflows/django.yml`, `.github/workflows/docker-build-push.yml`, `.github/dependabot.yml`
- [x] F-013: Drop `strategy`/matrix and set `python-version: "3.13"`. Use `branches: [ main ]`. Use `actions/checkout@v5`, `actions/setup-node@v5`, `actions/setup-python@v6` (or a pinned `astral-sh/setup-uv` with `enable-cache: true` replacing the pip and uv lines). Use `uv sync --locked --extra dev`. Delete the `.env` step.
- [x] F-018: Pin `appleboy/ssh-action` to its latest v1 full commit SHA with a `# vX.Y.Z` comment. If script_stop is dropped, add `set -e` as the first script line.
- [x] F-054 + F-101: Add `.github/dependabot.yml` with monthly `github-actions` (`/`), `docker` (`/infra`), `uv` (`/`) and `npm` (`/`), each grouping minor and patch updates into one PR.

### 3b. CI Node aligned with Dockerfile (`chore/ci-node-22`), risk low
Files: `.github/workflows/django.yml`, `.github/workflows/docker-build-push.yml`, `.env.example`
- [x] F-014: Set `node-version: 22` in django.yml (matching `infra/Dockerfile:2` node:22-slim). Delete the setup-node and "Build CSS (preflight)" steps in docker-build-push.yml:34-42.
- [x] F-055 + F-112: Delete the build job `env:` (16-25), all IMAGE_NAME lines (workflow :10, :52, :105 and `.env.example:30`) and the `master` refs (:5, :86, :100-101). Keep the `.env` heredoc.

### 3c. Docker image installs from uv.lock (`chore/docker-uv-lock`), risk medium
Files: `infra/Dockerfile`, `pyproject.toml`
- [x] F-045: Replace Dockerfile:26-27 with `COPY --from=ghcr.io/astral-sh/uv:<pinned> /uv /bin/uv` and `RUN uv export --frozen --no-dev --no-emit-project -o /tmp/req.txt && uv pip install --system --no-cache-dir -r /tmp/req.txt && uv pip install --system --no-cache-dir --no-deps .`. Delete the `[tool.uv] pip` table (pyproject.toml:29-30). Compare `pip freeze` in the old and new images.

### 3d. Transitive pins (`chore/deps-transitive-pins`), risk low, after 3c
- [x] F-050: Remove asgiref, packaging and tzdata from dependencies. Use `"pyjwt>=2.15.0"` and `"sqlparse>=0.6.0"`. Run `uv lock`.

### 3e. Pillow (`chore/deps-pillow-12.3`), risk low
- [x] F-052: `pillow==12.3.0`, then `uv lock --upgrade-package pillow`.

### 3f. Celery (`chore/deps-celery-5.6`), risk low
- [x] F-051: `celery[redis]==5.6.3`, `uv lock`, then check in `make dev-up` that the worker and beat log scheduled runs.

### 3g. Routine minor bumps (`chore/deps-minor-bumps`), risk low
- [x] F-106 (part A): django-environ, markdown, requests and ruff to their latest versions, `uv lock`, then `npm update` (tailwindcss, @tailwindcss/cli, daisyui).

### 3h. gunicorn 26 and pymdown-extensions 12 (`chore/deps-gunicorn-pymdown`), risk medium
- [x] F-106 (part B): Read both changelogs, bump, and run `uv lock`. The arithmatex test covers pymdown, and `make dev-up` checks that gunicorn starts.

### 3i. PostgreSQL 18 on a fresh database (`chore/deps-postgres-18`), risk medium
No data migration (R2): the new database starts empty on dev and on the new droplet; the owner re-enters projects, tags, profile and thumbnails in admin, and heatmap and blog markdown refill from GitHub.
- [x] F-007: Use `image: postgres:18` in both compose files. Mount the data volume at `/var/lib/postgresql` (the postgres:18 image moved PGDATA). Use new volume names (`postgres18_data`, `postgres18_dev_data`) so the old PG13 volumes stay untouched; never run `docker volume rm`. Check with `make dev-up` that db starts and `migrate` runs on the empty volume.
- [x] F-007 (runbook): Write a "New droplet bootstrap" section in `docs/implementation.md`: create the droplet with DO backups on, add the DO Monitoring alert (disk > 85%, email), install Docker, clone the repo, write the server `.env` (incl. ADMIN_BASIC_USER/HASH), set the GitHub secrets (SERVER_HOST, SERVER_USER, SSH_PRIVATE_KEY, SERVER_SSH_FINGERPRINT), run the first deploy, `createsuperuser`, re-enter content in admin, trigger both sync jobs from /about, then delete GHCR_PAT. Merge in the first-deploy checklist items from Phases 2 and 10.

### 3j. Django 6.1 (`chore/deps-django-6.1`), risk medium, after 3i
- [x] F-011: Pin `django==6.1.2` (or the latest 6.1.x on PyPI) and run `uv lock --upgrade-package django`. Read the 6.0 and 6.1 release notes for removals. Run `make verify` and also run the suite against Postgres 18 locally (`DB_ENGINE=django.db.backends.postgresql` via dev compose), because CI uses SQLite. Then run `manage.py check --deploy`.

**End of phase: one report for all sub-steps.**

---

## Phase 4: Correctness bugs (includes high F-004 and F-008)

- **Goal:** fix confirmed functional bugs.
- **Branch:** `fix/audit-p4-bugs`
- **Files:** `django/main/static/js/mobile-menu.js`, `django/main/templates/base.html`, `pages/about.html`, `projects/detail.html`, `projects/index.html`, `django/main/static/src/css/input.css`, `django/main/markdown_sync.py`, `django/main/models.py` (+ one migration for validators), `django/main/views.py`, `django/config/urls.py`, `django/main/urls.py`, `django/main/middleware.py`, `django/main/tasks.py`, `django/main/github_client.py`, `django/config/settings.py`, `infra/docker-compose.prod.yml`, the matching tests
- **Verify:** `make verify`, plus a manual check of the mobile menu in Playwright WebKit or on an iPhone, and visual checks of the headings and titles.
- **Risk:** low to medium (F-003 and F-040 change runtime paths).

- [x] F-008: Add `restart: always` to `web` and `caddy` in prod compose. Optionally assert `count("    restart: always") == 6` in test_operational_files.py.
- [x] F-004 + F-079: In mobile-menu.js:10, toggle `dropdown-open` on `button.parentElement` instead of `hidden`. Remove `hidden` from base.html:42. In the Escape handler, return early unless `aria-expanded === "true"`. Change `lg:hidden` to `md:hidden` at base.html:25.
- [x] F-029: Wrap input.css:9-17 in `@layer base { }`.
- [x] F-034 + F-111: Rename the `page_name` block to `title` in about.html:3 and detail.html:4. In base.html:8 use `{% block title %}{{ site_name|default:"My Portfolio" }}{% endblock %}`. projects/index.html gets `Projects | {{ site_name|default:"My Portfolio" }}`. Add one test on the detail page `<title>`.
- [x] F-003: In `sync_project_markdown`, skip the write when the stored bytes equal the new text (counted as success). When the content changed and a file exists, overwrite it in place with `storage.open(name, "wb")`. Call `markdown_file.save` only when there is no file. Tests: two syncs with different content keep the same name; an identical sync does not rewrite the file.
- [x] F-040: Move `templates/errors/404.html` and `500.html` to `templates/404.html` and `500.html`. Delete views.py:90-97 and config/urls.py:32-34. Rewrite ErrorHandlersTest (test_views.py:22, 650-664) against `django.views.defaults`.
- [x] F-025: Add `def clean(self): self.name = self.name.upper()` on Tag.
- [x] F-026: In `_delete_file_field`, capture name and storage and run `transaction.on_commit(lambda: storage.exists(name) and storage.delete(name))`. Add `captureOnCommitCallbacks(execute=True)` to the cleanup tests.
- [x] F-059: `[h.strip() for h in env.list(...) if h.strip()]` at settings.py:43 and :107.
- [x] F-067: Before the 401/403 check at both call sites, raise GitHubUpstreamError("GitHub rate limit exceeded") when the status is 403 and `X-RateLimit-Remaining == "0"` or `Retry-After` is present. Add one mocked test.
- [x] F-076: Remove the `blog_slug` parameter from `sync_project_markdowns_task` (tasks.py:30,37-38) and `run_markdown_sync_task` (views.py:426-437), and update test_views.py:551.
- [x] F-077: Delete the 6 `last_success_at=None` and the 3 `last_failure_at=None` assignments, and update test_tasks.py:189,231,331 to check that the timestamps are kept.
- [x] F-089: Turn `home/` into `RedirectView.as_view(pattern_name="home", permanent=True)` without a name. Update test_urls.py:24 and test_middleware.py:28-30, and drop `/home/` from middleware.py:13.
- [x] F-120 + F-128: Add a UTF-8 decode validator and help_text on `markdown_file` (help_text: replaced by the GitHub README on sync when Blog is on). Add a `validate_str_list` validator on `tech_stack` and `tools_libraries`. One `makemigrations` (a no-op AlterField), plus one full_clean test.

**End of phase: report what changed and the verification output.**

---

## Phase 5: Simplification

- **Goal:** delete duplicated, dead and over-general code with no behaviour change.
- **Branch:** `refactor/audit-p5-simplify`
- **Files:** `django/main/tasks.py`, `views.py`, `heatmap.py`, `github_client.py`, `markdown_sync.py`, `context_processors.py`, `models.py`, `django/config/settings.py`, templates (`about.html`, `project_card.html`, `base.html`, `detail.html`, `hero_section.html`), `infra/Caddyfile`, `infra/docker-compose.*.yml`, `infra/scripts/` (deleted), `Makefile`, `.gitignore`, `.env.example`, tests
- **Verify:** `make verify`; `docker compose -f infra/docker-compose.prod.yml config` diff before and after (F-047); Caddy validate (F-100); `git status --ignored --porcelain` diff (F-057); a visual check of /about.
- **Risk:** low (F-023 is medium: GitHub client rewrite).

- [ ] F-033: Delete `schedule_next`, `_maybe_schedule_next_refresh` (tasks.py:250-257) and its call sites, `views._schedule_next_heatmap_refresh` (views.py:189-197), the beat kwargs (settings.py:218) and the apply_async patch (test_views.py:240,243,278). Update test_views.py:70,203.
- [ ] F-030: Add a `_finish(status, state, total, updated, error="")` helper (sets the fields, the success/failure timestamp, saves and logs), used at all 5 sites. Delete tasks.py:119-143 and the token import. In tests 294 and 317 use `override_settings(GITHUB_HEATMAP_TOKEN="")`. Compute `last_error` once.
- [ ] F-068: Delete the unused override params (`github_token=`, `ttl_minutes=`, `graphql_url=`, the markdown `timeout=`). `get_configured_github_token` becomes `return settings.GITHUB_HEATMAP_TOKEN or None`.
- [ ] F-023: Use one GraphQL `viewer { login contributionsCollection { ... } }` call returning `(login, days)`, with a single `try/except (KeyError, TypeError)` raising GitHubUpstreamError, and `any()` for the auth substrings. Delete `fetch_authenticated_user` and heatmap.py:82-86, and keep one day-type filter. Update the test_heatmap.py mocks.
- [ ] F-070: Drop the try/except around `requests.get` (markdown_sync.py:100-110) and the Content-Length block (:112-121). Use `list(dict.fromkeys(candidates))`, catch `(OSError, ValueError)` at :154, and catch `requests.RequestException` in github_client.
- [ ] F-061: Delete `STATICFILES_STORAGE` (unless F-099 step 2 is planned, in which case replace it with `STORAGES`), `environ.Env(DEBUG=...)` (use plain `Env()`), `CELERY_RESULT_BACKEND/SERIALIZER/ACCEPT_CONTENT` (settings, both compose files, `.env.example:44`), one `DEFAULT_AUTO_FIELD`, the commented prints, the default AUTHENTICATION_BACKENDS and the empty TEMPLATES DIRS. Translate the Polish comments. Check with `collectstatic --dry-run`.
- [ ] F-091: Build the timeline from `Project.STATUS_CHOICES` and delete `status_labels` and `status_order`.
- [ ] F-092: `_calculate_last_30_days_total` becomes a one-line `sum(...)` with `start <= date <= today`.
- [ ] F-093: Add `disk_level(free_gb)` in tasks.py next to the thresholds, used by `views._get_disk_info` and the task.
- [ ] F-094: Delete `heatmap_component_visible` (and its if/endif at about.html:47,257), the `blog_markdown_content` key and the unused hero class slots. Use `with project.markdown_file.open("rb") as f: return f.read().decode("utf-8-sig")`.
- [ ] F-065: Add a `PortfolioProfile.get_active()` classmethod used at context_processors.py:28 and markdown_sync.py:33,63.
- [ ] F-084: In about.html, replace the variant loop with direct consts, delete the `daisy` tooltip branch and the `contribution_count` fallback (also views.py:231), and use `COLORS[day.level || 0]`.
- [ ] F-086: Merge the two `<img>` blocks in project_card.html into one.
- [ ] F-081: Delete `hover:bg-primary-focus` (base.html:165), `menu-compact` (base.html:42) and `not-prose` (detail.html:26).
- [ ] F-100: In the Caddyfile use `@files path /static/* /media/*` with one `handle @files { root * /srv; file_server }`, keeping the F-044 headers (`header /media/* ...`). Run `caddy fmt` and `caddy validate`.
- [ ] F-047: Delete the SECRET_KEY, DJANGO_DEBUG, ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS lines from the 6 environment blocks (prod and dev). The `docker compose config` output must stay the same.
- [ ] F-049: In the Makefile, dev-up becomes `@test -f .env || { cp .env.example .env && echo "Created .env from .env.example."; }` (a Makefile text change only; the agent does not run `make dev-up` on a checkout without .env). dev-status copies the prod-status `docker ps` line with label `my-django-portfolio-dev`. Delete `infra/scripts/`, `tests/test_operational_helpers.py` and `tests/test_operational_files.py:34-37`.
- [ ] F-057: Cut `.gitignore` to the Python basics, `.env*`, the celerybeat files and the custom tail (:166-180), and drop the duplicate line. The ignored set must be unchanged.

**End of phase: report what changed and the verification output.**

---

## Phase 6: Module and architecture changes

- **Goal:** remove duplicated state and configuration.
- **Branch:** `refactor/audit-p6-architecture`
- **Files:** `django/main/views.py`, `models.py` (+ migration), `tasks.py`, `admin.py`, `markdown_sync.py`, `templates/projects/components/project_footer.html`, `projects/detail.html`, tests
- **Verify:** `make verify`; `makemigrations --check` passes after the new migration; check the admin jobs panel on /about as staff in `make dev-up`.
- **Risk:** medium (a schema migration in F-072, a data migration in F-069).

- [ ] F-041: The jobs panel iterates `settings.CELERY_BEAT_SCHEDULE` with a `{task_name: label}` dict (including the disk task). Next run is `now + entry["schedule"].remaining_estimate(now)`, with the beat path `main.tasks.X` mapped to `main.X`. Delete `interval_minutes`.
- [ ] F-072: Drop `TaskExecutionStatus` (migration; also drop `last_success_at` and `last_failure_at` if unused). Tasks write only the log row. views.py:265-271 reads the latest log per task. Update the admin and test_tasks/test_models assertions. Do this after F-030 and F-078.
- [ ] F-119: Register PageView with a ModelAdmin whose `has_add_permission` and `has_delete_permission` return False, with `readonly_fields = ("count",)`.
- [ ] F-069: Add a data migration that fills empty `github_url` on `blog=True` projects exactly as the code computes it today (Q15). Then delete `BLOG_REPO_PATHS`, `get_repo_path`, `_active_github_username` and the fallbacks (markdown_sync.py:13-41, 59, 63-65, 80-88). project_footer.html:6 uses `project.github_url`, and `repo_path` is dropped from the blog_detail context and detail.html:31.

**End of phase: report what changed and the verification output.**

---

## Phase 7: Library replacements

- **Goal:** replace or remove the dependencies the audit flagged.
- **Branch:** `chore/audit-p7-libraries` (one commit per item)
- **Files:** `pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`, `infra/Dockerfile`
- **Verify:** `make verify`; `make dev-up` and load /, /about and a blog page against Postgres; `npm run build:css:prod`.
- **Risk:** low.

- [ ] F-107: Replace `psycopg2-binary` with `psycopg[binary]==<latest, checked on PyPI>` (the ENGINE stays the same), then `uv lock`.
- [ ] F-105: `npm uninstall @catppuccin/daisyui`, then `npm run build:css:prod`.

**End of phase: report what changed and the verification output.**

---

## Phase 8: Tests

- **Goal:** cover the confirmed untested branches and remove vacuous tests.
- **Branch:** `test/audit-p8-coverage`
- **Files:** `django/main/tests/test_tasks.py`, `test_markdown_sync.py`, `test_views.py`, `test_urls.py`, `test_models.py`, `test_heatmap.py`, `tests/test_operational_files.py`, `.github/workflows/django.yml`
- **Verify:** `make verify` (the new tests fail when the guarded line is reverted; spot-check one).
- **Risk:** low.

- [ ] F-031: Test that `sync_project_markdown` raising RuntimeError for 1 of 2 projects gives PARTIAL_SUCCESS with `task_exception`, and that the heatmap fetch returning `(None, "boom")` gives FAILURE, a log row and `snapshot.last_error`. Skip the blog_slug test (removed in F-076).
- [ ] F-037: Using the existing `_make_mock_response`, test a 404 on the first candidate URL with a 200 on the second, and an HTML body giving download_failed with the old file kept. (The Content-Length block is already gone via F-070.)
- [ ] F-039: Patch `main.views.shutil.disk_usage` (fake as in test_tasks.py:342-347): 0.96 GB free gives `critical`, 1.96 GB gives `warning`.
- [ ] F-066: Turn the 401 test into a subTest over 401 -> GitHubAuthError, 403 -> GitHubAuthError, 500 -> GitHubUpstreamError, and add one test for the "temporarily unavailable" mapping (adapted to the F-023 client).
- [ ] F-087: Copy the 2 thumbnail cleanup tests for `markdown_file`, and extend test_views.py:622 with camo.githubusercontent.com and github.com images that must remain.
- [ ] F-088: Remove the negative assertNotContains checks on removed UI (test_views.py:83,104-109,211-213; test_urls.py:32-33), rename `test_task_3_*` to descriptive names, and assert exact status codes.
- [ ] F-097: Test that `delay` raising gives a 302 and an error message for both admin-tool views.
- [ ] F-053: Trim test_operational_files.py to the #55/#57 ordering checks. In the django.yml job add `cp .env.example .env && docker compose -f infra/docker-compose.prod.yml config -q` (this runs on the CI runner only, never locally).

**End of phase: report what changed and the verification output.**

---

## Phase 9: Frontend (accessibility, SEO, UX)

- **Goal:** fix the confirmed frontend, accessibility and SEO gaps.
- **Branch:** `feat/audit-p9-frontend`
- **Files:** `django/main/templates/base.html`, `pages/about.html`, `projects/index.html`, `projects/detail.html`, `components/*.html`, `projects/components/*.html`, `django/main/static/js/theme-toggle.js`, `projects-filters.js`, `django/main/static/images/favicon.svg` (new), `django/main/context_processors.py`, `django/main/admin.py`, `infra/Caddyfile`, optional `django/config/{settings,urls}.py` and `django/main/sitemaps.py` (F-116)
- **Verify:** `make verify`; `make dev-up` and check /, /projects/, /about and a blog page in light and dark themes and at 375px; Caddy validate.
- **Risk:** low.

- [ ] F-028: Add an inline head script in base.html before the stylesheet: `try{var t=localStorage.getItem("theme");if(t==="dim2")document.documentElement.dataset.theme=t}catch(e){}`. Wrap the storage calls in theme-toggle.js in try/catch and delete `legacyThemeMap`.
- [ ] F-036: Delete the skeleton (index.html:40-60) and `hidden` (:62). In projects-filters.js delete :8, :89-90 and the skeleton and grid parts of the :11 guard.
- [ ] F-074: Remove the debounce wrappers and call `applyFilters` directly on input and at :69 and :84.
- [ ] F-075: Render `aria-pressed` in the template (true on All, false on tags) and set it in the loop at projects-filters.js:76.
- [ ] F-080: Add `aria-current="page"` via `request.resolver_match.url_name` on the 6 nav links and `aria-hidden="true"` on the SVG at :167. Delete the duplicate footer link at :158.
- [ ] F-083: In timeline_section.html use `<details class="collapse ..." name="timeline-accordion" {% if section.checked %}open{% endif %}>` with `<summary class="collapse-title">`.
- [ ] F-085: The heatmap grid gets `role="img"` and an aria-label summary set in renderGrid. Add `aria-hidden` on the month row, drop the per-cell aria-label (keep title), and add `role="alert"` on the error box.
- [ ] F-127: Add `{% if sidebar_project.id == project.id %}aria-current="page"{% endif %}` at blog_projects_sidebar.html:8.
- [ ] F-110: In base.html add `<meta name="description" content="{% block meta_description %}{{ profile_home_intro }}{% endblock %}">`, overridden in about (profile_about_intro) and detail (project.short_description).
- [ ] F-121: Add og:title (own `og_title` block), og:description, og:type, og:url (`request.build_absolute_uri`), an absolute og:image (thumbnail or default image) and `twitter:card`. Override them on detail.
- [ ] F-122: Add `static/images/favicon.svg` and `<link rel="icon" type="image/svg+xml">`, plus Caddy `redir /favicon.ico /static/images/favicon.svg`.
- [ ] F-132: Caddy `respond /robots.txt "User-agent: *\nDisallow: /admin/\n" 200`, before reverse_proxy.
- [ ] F-124: In the context processor return `''` instead of `'#'` (lines 31, 32, 34, 44). Guard the links with `{% if %}` in about_content.html, base.html and project_footer.html:6.
- [ ] F-126: Delete the `{% elif project.github_url %}` branch (timeline_project_item.html:13-14).
- [ ] F-125: `<time datetime="{{ project.date|date:'Y-m' }}">`.
- [ ] F-123: Add `target="_blank" rel="noopener noreferrer"` to the header social links (base.html:63, :72).
- [ ] F-117: ProjectAdmin: `list_display` (title, status, blog, blog_url, date), `list_filter` (status, blog, tags), `filter_horizontal = ("tags",)`. TaskExecutionLogAdmin: `list_filter` (task_name, last_status) and `date_hierarchy = "created_at"`.
- [ ] F-116: Add `django.contrib.sitemaps`, a blog-project sitemap and a static-pages sitemap, a `sitemap.xml` route and a Sitemap line in the F-132 robots.txt.

**End of phase: report what changed and the verification output.**

---

## Phase 10: Ops

- **Goal:** zero-downtime, guarded deploys, backups, alerts and bounded growth.
- **Branch:** `ops/audit-p10-ops`
- **Files:** `.github/workflows/docker-build-push.yml`, `infra/docker-compose.prod.yml`, `infra/docker-compose.dev.yml`, `infra/Dockerfile`, `infra/scripts/wait-for-db.sh` (delete), `django/config/settings.py`, `django/main/middleware.py`, `django/main/tasks.py`, `docs/implementation.md`, `tests/test_operational_files.py`, `django/main/tests/test_middleware.py`
- **Verify:** `make verify`; `make dev-up` (db reports healthy, web/worker/beat start without the sleep); `docker compose -f infra/docker-compose.prod.yml config -q` with a CI-style env.
- **Risk:** medium (the deploy script and startup ordering change). The first deploy after merge should be watched by the owner.

- [ ] F-001: Add workflow-level `concurrency: {group: deploy-prod, cancel-in-progress: false}`. Replace docker-build-push.yml:108-109 with `up -d --remove-orphans --wait`, and update tests/test_operational_files.py:79-95. Also (A9) push `:${{ github.sha }}`, use `image: ghcr.io/stokuj/my-django-portfolio:${IMAGE_TAG:-latest}`, and `git checkout --detach ${{ github.sha }}` with `IMAGE_TAG` on the server.
- [ ] F-048: Add a `pg_isready -h 127.0.0.1 -U $${POSTGRES_USER} -d $${POSTGRES_DB}` healthcheck on db (both compose files, interval 5s, retries 12), with `db: {condition: service_healthy}` for web, worker and beat. Delete the `entrypoint:` lines, `wait-for-db.sh`, Dockerfile:29-30 and `postgresql-client`, and drop the worker `sleep 45` and `WORKER_START_DELAY_SECONDS` (`.env.example:47`).
- [ ] F-009: Gunicorn command `--workers 1 --threads 4 --timeout 60 --access-logfile -` (prod.yml:46) (A8).
- [ ] F-024: VisitorCountMiddleware checks `request.COOKIES.get("has_visited")` and sets it on the response with `set_cookie(..., max_age=settings.SESSION_COOKIE_AGE, secure=settings.SESSION_COOKIE_SECURE, httponly=True, samesite="Lax")` instead of the session. Run test_middleware.py.
- [ ] F-062: `CELERY_TASK_TIME_LIMIT = 600` and `CELERY_TASK_SOFT_TIME_LIMIT = 540` in settings.
- [ ] F-078: In `_log_task_execution`, after the create, `TaskExecutionLog.objects.filter(created_at__lt=timezone.now() - timedelta(days=90)).delete()`.
- [ ] F-010: DO droplet backups are in the bootstrap runbook (3i). Agent: add a restore note to docs/implementation.md and a pre-deploy `pg_dump -Fc` to `~/backups/pre-deploy-$(date +%F-%H%M).dump` plus `find ~/backups -mtime +14 -delete` in the deploy script before `up`.
- [ ] F-032: The DO disk alert is in the bootstrap runbook (3i). Agent: note in docs/implementation.md that disk alerting lives in DO Monitoring.

**End of phase: report what changed and the verification output.**

---

## Phase 11: Performance

- **Goal:** cheap wins only.
- **Branch:** `perf/audit-p11-perf`
- **Files:** `infra/Caddyfile`, `django/config/settings.py`, `django/main/views.py`, `django/main/static/images/hero-bg*.png` (replaced by WebP), the templates that include hero_section, optionally `django/main/context_processors.py` and `models.py` (signals)
- **Verify:** `make verify`; `make dev-up` and check that the hero images render; `curl -sI -H 'Accept-Encoding: gzip'` against /static on the Caddy stack shows `Content-Encoding`.
- **Risk:** low (F-099 step 2 is medium: manifest storage).

- [ ] F-099 (step 1): Add `encode zstd gzip` to the apex Caddy block.
- [x] F-099 (step 2): Skipped (A10). Was: Use `STORAGES = {"default": FileSystemStorage, "staticfiles": ManifestStaticFilesStorage}`, add `collectstatic --noinput` to `make verify`, check the dynamic `{% static hero_background %}` values, and only then add `header /static/* Cache-Control "public, max-age=31536000, immutable"` (never on /media).
- [ ] F-082: Delete `hero-bg3.png`, re-encode `hero-bg.png` and `hero-bg2.png` to WebP at q70, and point the 5 `hero_background=` include arguments at the new files.
- [ ] F-022: Set `"CONN_MAX_AGE": 60, "CONN_HEALTH_CHECKS": True` in `DATABASES["default"]`.
- [ ] F-096: Sidebar query: `Project.objects.only("id","title","blog","blog_url","github_url","date").order_by("-date")`.
- [x] F-064: Skipped (A10). Was: cache only the active profile with `cache.get_or_set` (300s, LocMem), cleared by post_save and post_delete on PortfolioProfile. Keep visitor_count uncached.
- [x] F-071: Won't fix (A10).

**End of phase: report what changed and the verification output.**

---

## Phase 12: Docs

- **Goal:** the docs match the code at the end of the plan.
- **Branch:** `docs/audit-p12-docs`
- **Files:** `docs/implementation.md`, `docs/architecture.md`, `docs/frontend.md`, `README.md`, `CLAUDE.md`, `django/config/settings.py` (beat key), `django/main/tasks.py` and `django/main/tests/test_tasks.py` (healthcheck_task), `docs/audit/2026-10-14/`
- **Verify:** `make verify`; grep the docs for removed names (`healthcheck_task`, `wait-for-db`, `infra/scripts`, `django-ci.yml`).
- **Risk:** low.

- [ ] F-098 + F-130: Delete `healthcheck_task`, its test (test_tasks.py:337-338 and the import at :14) and implementation.md:36. Document all 3 beat entries (heatmap hourly, markdown every 2h, disk daily 06:00) in implementation.md, architecture.md:146 and the CLAUDE.md beat schedule.
- [ ] F-063: Rename the beat key to `sync-project-markdowns-every-2h` (settings.py:220).
- [ ] F-129: In architecture.md:6, say "In production (infra/docker-compose.prod.yml)" and add one line on dev compose (no Caddy, runserver on 127.0.0.1:8000).
- [ ] F-131: In the frontend.md diagram, add Errors --> Hero, list both blog sidebar partials, and add a `HeroContent["components/hero/*_content.html"]` node.
- [ ] F-113: Drop "The main landing page" at README.md:67.
- [ ] F-114: Change "Python 3.13+" to "Python 3.13" at README.md:106.
- [x] F-043: Done before Phase 1 (R5): `docs/superpowers/` removed, this plan moved to `docs/audit/2026-10-14/PLAN.md`.
- [ ] Q21: `git rm -r docs/audit/2026-10-14/find docs/audit/2026-10-14/verify`; keep `SYNTHESIS.md`, `completeness.md`, `README.md`, `DECISIONS.md` and this plan. Drop the `verify/` pointer at the top of this file.
- [ ] Final sweep: update CLAUDE.md, README.md and the docs for every structural change made in Phases 1-11 (Makefile targets, removed scripts, healthchecks, deploy steps).

**STOP: final report.**

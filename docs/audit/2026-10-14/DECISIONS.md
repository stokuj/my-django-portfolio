# Audit decisions (owner answers)

Phases read this file instead of asking. Ask mid-phase only when no decision covers the case.

## Context (2026-10-15)

- Production is off. The old droplet is archived; a new droplet will be created later.
- All work runs locally until then. Deploy-related phases prepare code and runbooks, nothing runs on a server.

## Settled

| # | Decision | Rejected |
|---|----------|----------|
| Q1 | Merge each phase branch locally into `dev` with `--no-ff`. Push and PR `dev → main` only on the owner's "push". | PR per phase to `main`; auto PR after each phase |
| Q2 | No STOP after phases. Stop only on a red `make verify`, an error, or an [OWNER] step. | STOP after every phase; STOP after phases 2, 3, 6, 10 |
| Q4 | Keep the `Co-Authored-By` trailer in `c2d8534` and `2bfafbe`. | Rewrite the two commits |
| Q6 | Caddy `basic_auth` in front of `/admin*`. | django-axes; nothing |
| Q7 | HSTS stays as is; skip F-060. `check --deploy --fail-level WARNING` must pass without silencing. | env toggles defaulting to False; drop `preload` only |
| Q9 | Keep `127.0.0.1:15432` in prod compose (owner uses an SSH tunnel). Skip F-103. | Remove `ports` |
| Q10 | Django 6.1.2. | 5.2 LTS; stay on 5.1 |
| Q11 | PostgreSQL 18 (mount path changes to `/var/lib/postgresql`). | 17; 16 |
| Q13 | Dependabot for actions, docker, uv, npm; monthly; minor+patch grouped. | actions+docker only; none |
| Q14 | Delete `TaskExecutionStatus`; the about panel reads the latest `TaskExecutionLog` per task (`.first()` per task, SQLite-safe). | keep model; delete logs |
| Q15 | Data migration fills empty `github_url` the way code computes it today, then delete `BLOG_REPO_PATHS`. | owner fills in admin; keep map |
| Q16 | Phase 7 scope: psycopg2 → psycopg 3.3.6, remove `@catppuccin/daisyui`. | replace Celery with cron; bleach → nh3 |
| Q17 | Full SEO: meta description, OG/Twitter (og:image = hero), `robots.txt`, sitemap. No new deps. | meta+robots only; nothing |
| Q18 | Agent draws a simple SVG monogram favicon. | owner file; none |
| Q19 | Agent adds pre-deploy `pg_dump` (14-day retention) and a restore note now. Owner enables DO droplet backups and the 85% disk alert when creating the new droplet. | free only; nothing |
| Q21 | After Phase 12 delete `find/` and `verify/`; keep `SYNTHESIS.md`, `completeness.md`, `README.md`, this file. | keep all; delete all |

## Assumptions (all accepted)

- A1 Tests run on SQLite in `make verify` and CI; Postgres checked by hand at the Django upgrade.
- A2 MathJax pinned to 3.2.2 with SRI, no v4.
- A3 `actions/*` on major tags; third-party actions on full SHA.
- A4 Bump bleach 6.2.0 → 6.4.0 in 3g.
- A5 F-004 checked in Playwright WebKit; owner opens the menu once on an iPhone.
- A6 Remove `infra/scripts/` in favour of Makefile one-liners; GitHub client uses one GraphQL query (F-023).
- A7 Theme: fix the flash only, no system-preference following.
- A8 gunicorn `--workers 1 --threads 4 --timeout 60 --access-logfile -`.
- A9 Tag images `:sha`; compose reads `IMAGE_TAG`; a few seconds of downtime per deploy is fine.
- A10 Task log retention 90 days; skip F-099 step 2, F-064, F-071.

## Round 2

| # | Decision | Rejected |
|---|----------|----------|
| R1 (Q3) | Owner writes "faza N"; the orchestrator session spawns one subagent for that phase, then reviews, merges into `dev` and reports. The owner's "faza N" is the gate between phases. | owner runs a prepared prompt per phase; one "start" runs all phases |
| R2 (Q12) | No data migration. PostgreSQL 18 starts empty on dev and on the new droplet; the owner re-enters projects, tags, profile and thumbnails in admin. Heatmap and blog markdown refill from GitHub. Phase 3 writes a new-droplet bootstrap runbook instead of a migration runbook. Leave the old PG13 volumes untouched. | `dumpdata`/`loaddata` from local dev; dump from the archived droplet |
| R3 (Q8) | Phase 2 ships the code for F-109, F-021, F-017, F-056. `check --deploy` runs locally with prod settings. The owner's steps (admin basic_auth password, `SERVER_SSH_FINGERPRINT`, delete `GHCR_PAT`) go into a first-deploy checklist for the new droplet. | defer the four items until the droplet exists |
| R4 (Q5) | F-008 and F-004 stay in Phase 4. | move them to the start |
| R5 (Q20) | Before Phase 1: move the audit plan to `docs/audit/2026-10-14/PLAN.md` and `git rm -r docs/superpowers`. | do it in Phase 12 |
| R6 | No change to the deploy job. Open the `dev → main` PR only once the new droplet exists. | `workflow_dispatch` deploy; merge now and accept a red deploy |

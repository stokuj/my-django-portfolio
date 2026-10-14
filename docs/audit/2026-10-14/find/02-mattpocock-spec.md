# mattpocock-spec

Scope: `docs/superpowers/specs/*.md` + matching `docs/superpowers/plans/*.md` vs implementation at `dev` HEAD (4416049). Spec axis only.

## 1. PostgreSQL 13 -> 16 upgrade from audit spec 4a never landed (reverted)
- Severity: high | Category: ops | Effort: M
- Location: `infra/docker-compose.prod.yml:3` (also `infra/docker-compose.dev.yml:3`); spec `docs/superpowers/specs/2026-05-14-codebase-audit-design.md` section 4a
- Problem: Spec 4a requires `postgres:13` -> `postgres:16` because 13 went EOL Nov 2025. Commit b8da60e reverted it ("migration deferred"); both compose files still pin `postgres:13`. As of 2026-10 the prod DB has had ~11 months with no security patches. The audit spec still reads as if 4a were done.
- Proposal: Track 4a as its own issue and run the dump/restore procedure. Change step 3 of that procedure: rename or keep the old volume instead of running `docker volume rm` until the restore has been checked. Bump dev compose in the same change.
- Risk: The major upgrade needs dump/restore on the droplet. Getting it wrong loses prod data.

## 2. `make verify` lints only infra scripts, not the Django code the spec required
- Severity: medium | Category: ci | Effort: S
- Location: `Makefile:39`; spec `docs/superpowers/specs/2026-05-08-issue-53-dev-prod-workflow-design.md` "Verification Scope" (`uv run ruff check .`)
- Problem: The spec requires `uv run ruff check .`. The implementation runs `uv run ruff check infra/scripts tests`. The issue-53 follow-up plan narrowed it on purpose, and it was never widened. Running `ruff check django` (migrations excluded) today gives 31 errors (15 I001, 11 E501, 3 F401, 2 F841). CI goes through `make verify`, so the app code is never linted.
- Proposal: Exclude `django/main/migrations` in `[tool.ruff]`. Run `ruff check --fix`, fix the rest by hand, then change the Makefile line to `uv run ruff check .`.
- Risk: Low. These are mostly import-order and line-length changes.

## 3. CI still builds CSS on Node 20 (EOL) after audit spec 4c moved the image to Node 22
- Severity: medium | Category: ci | Effort: S
- Location: `.github/workflows/django.yml:22`, `.github/workflows/docker-build-push.yml:37`; spec 4c
- Problem: Spec 4c moved `infra/Dockerfile:2` to `node:22-slim` because Node 20 EOL is April 2026. Both workflows still use `node-version: 20`. CI now checks the CSS build on a different Node version than the image uses, and that version is past EOL.
- Proposal: Set `node-version: 22` in both workflows.
- Risk: Negligible.

## 4. Dev Makefile targets use Python helpers where the spec asks for `docker ps --format`; prod already uses the shell
- Severity: low | Category: simplification | Effort: S
- Location: `Makefile:7`, `Makefile:19`, `infra/scripts/compose_status.py`, `infra/scripts/ensure_env.py`; spec issue-53 design "Status Output Design", issue-55 design
- Problem: The issue-53 spec asks for a table from `docker ps --format`. Instead, the implementation added `compose_status.py`, which re-implements table formatting (about 80 lines), plus `ensure_env.py`. Issue 55 then replaced both with shell one-liners for prod (`Makefile:22`, `Makefile:28-31`). Dev and prod now take two different routes for the same job.
- Proposal: Make `dev-status` the same `docker ps -a --filter label=com.docker.compose.project=my-django-portfolio-dev --format "table ..."` command. Change `dev-up` to `@test -f .env || cp .env.example .env`. Delete `infra/scripts/` and `tests/test_operational_helpers.py`, and update `test_makefile_uses_helper_scripts`.
- Risk: Low. The empty-result message changes from "No matching containers found." to a bare header.

## 5. Markdown filename grows on every sync now that the audit-1b signal handles cleanup
- Severity: low | Category: bug | Effort: S
- Location: `django/main/markdown_sync.py:168-172`, `django/main/models.py:251-262`; spec 1b
- Problem: Spec 1b moved deletion of the old file into the `pre_save` signal. Sync saves under the old file's basename while that file still exists, so the storage appends `_XXXXXXX` each time. Verified by simulation: `slug.md` -> `slug_d74c5Yg.md` -> `slug_d74c5Yg_5Up5iQ8.md` ... until it is truncated at 100 chars. This happens every 2h, even when the content has not changed.
- Proposal: Use the stable basename `f"{project.blog_url or f'project-{project.id}'}.md"`. Skip the write when the stored content equals `markdown_text`.
- Risk: Low. Existing long names get replaced on the next changed sync.

## 6. Audit spec 1b/2a paths without tests
- Severity: low | Category: tests | Effort: S
- Location: `django/main/tests/test_models.py:289-310`, `django/main/tests/test_views.py:613`
- Problem: Spec 1b covers `thumbnail` and `markdown_file`, but tests cover only `thumbnail`. `markdown_file` is the path the sync job uses (finding 5). Spec 2a allows `github.com` and `camo.githubusercontent.com`, but only `raw.githubusercontent.com` is asserted.
- Proposal: Add one test that `markdown_file` is deleted on replace/delete. Add one test with a `camo`/`github.com` image src.
- Risk: None.

## 7. `STATICFILES_STORAGE` kept by audit spec 3b is ignored by Django 5.1
- Severity: low | Category: simplification | Effort: S
- Location: `django/config/settings.py:181`; spec 3b ("Keep only the active `StaticFilesStorage` line")
- Problem: Django 5.1 (pinned `django==5.1.15`) removed the `STATICFILES_STORAGE` setting. Nothing in `.venv/.../django` reads it any more; only `STORAGES` counts. The spec calls this line "active", but it does nothing and misleads readers.
- Proposal: Delete the line. The default `STORAGES["staticfiles"]` is already `StaticFilesStorage`.
- Risk: None. Behaviour stays the same.

## 8. Specs/plans describe divergent or superseded details; all plans are merged but left open
- Severity: low | Category: docs | Effort: S
- Location: `docs/superpowers/specs/*`, `docs/superpowers/plans/*`
- Problem:
  - Audit spec 1c says the about-page disk panel reads `TaskExecutionStatus`. `views.py:240` reads `shutil.disk_usage("/")` live per request instead (the plan's Task 9 already did this).
  - Spec 2b wants an inline `.env.example` comment. It was deliberately moved to its own line (`.env.example:1`) because an inline comment breaks `env.bool()` (d2b6257).
  - Spec 3c says `timeout=15`; the code uses 20 (`markdown_sync.py:99`).
  - The issue-53 spec still describes a root `docker-compose.prod.yml` and project `my-django-portfolio-prod`. Both were superseded by the move to `infra/` and by issue 55.
  - The issue-51 plan has no spec (removed in eddf077).
  - Every plan still shows its checkboxes unchecked (0 done in 5 of 6 plans), even though PRs #52/#54/#56/#58/#59 are merged.
- Proposal: Move the specs/plans for #51/#53/#55/#57 to `docs/superpowers/archive/`, or delete them. In the audit spec, mark 1c/2b/3c as amended and 4a as open (finding 1).
- Risk: None.

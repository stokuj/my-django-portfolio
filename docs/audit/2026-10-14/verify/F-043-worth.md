# F-043 (worth) - Obsolete/divergent specs and plans in docs/superpowers

**Verdict:** CONFIRMED (facts hold), severity overstated
**Confidence:** high
**Adjusted severity:** low

## Reasoning

Facts verified at HEAD:
- 6 plans + 5 specs, 4479 lines total under `docs/superpowers/`. Plans are almost all unchecked (e.g. `plans/2026-05-14-codebase-audit.md`: 64 `- [ ]`, 0 `- [x]`; only `plans/2026-05-09-issue-53-followup-fixes.md` has 8 checked).
- 1c: spec says the about-page disk panel reads `TaskExecutionStatus` (`specs/2026-05-14-codebase-audit-design.md:40`); the code calls `shutil.disk_usage("/")` live (`django/main/views.py:240-241`).
- 2b: spec prescribes the inline comment `DJANGO_DEBUG=True  # DEVELOPMENT ONLY ...` (`specs/2026-05-14-codebase-audit-design.md:74`); d2b6257 removed it because it broke `env.bool()`.
- 3c: spec says `timeout=15` (`specs/...-codebase-audit-design.md:96`); code uses `timeout=20` (`django/main/markdown_sync.py:99,135`).
- 4a: spec gives the PG 13 -> 16 procedure (`specs/...-codebase-audit-design.md:114`); b8da60e reverted it, and `infra/docker-compose.prod.yml:3` is still `postgres:13`.
- Root `docker-compose.prod.yml` naming: `specs/2026-05-08-issue-53-dev-prod-workflow-analysis.md:11,88`; the files live in `infra/`.
- Nothing outside `docs/superpowers/` links to it (no references in README, CLAUDE.md, architecture.md, implementation.md).

Why only low: these are dated, point-in-time design notes, not reference docs. Nobody reads them to run or deploy the app, and nothing links to them. The real risk is small: an agent or reader takes a stale spec as current, for example 2b, which would bring back a known bug. That is "nice to have", not "should fix". The one item that matters, PG 13 EOL (4a), is already tracked as F-007 (high, ops), so this finding adds nothing there.

Part of the proposal is not worth doing: "mark 1c/2b/3c as amended and 4a as open" means editing historical records to follow the code. That is churn, and they will drift again. Pick one of two options:

## Better proposal

Smallest diff: `git rm -r docs/superpowers/` (no inbound links, history stays in git; the PRs #51/#53/#55/#57/#59 hold the context). Effort S.
If the owner wants to keep them: add one line to each file, or one `docs/superpowers/README.md`, saying "Historical point-in-time notes; code and docs/architecture.md are the source of truth." Do not amend individual sections. Track 4a only through F-007.
Note: the new `docs/audit/2026-10-14/` will age the same way, so the same policy should apply to it.

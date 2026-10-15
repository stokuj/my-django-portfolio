# F-043 — Obsolete/divergent specs and plans in docs/superpowers (reproduce)

**Verdict:** CONFIRMED (minor overstatement)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- Volume: 6 plans + 5 specs under `docs/superpowers/`, 4479 lines total (`wc -l`). Matches "~4.4k".
- Checkboxes: 166 unchecked `- [ ]` across plans; only `plans/2026-05-09-issue-53-followup-fixes.md` has 8 checked (e.g. :271). "Unchecked" is true for 5 of 6 plans, not all.
- 1c: spec `specs/2026-05-14-codebase-audit-design.md:40` says the panel reads from `TaskExecutionStatus`; code computes live in `django/main/views.py:240-241` (`shutil.disk_usage("/")`). Diverges.
- 2b: spec :74 prescribes inline `# DEVELOPMENT ONLY` comment; `.env.example:2` is `DJANGO_DEBUG=True` with no inline comment (removed in d2b6257 because it broke `env.bool()`). Diverges, and following the spec would reintroduce a bug.
- 3c: spec :96 says `timeout=15`; `django/main/markdown_sync.py:99,135` use `timeout=20`. Diverges.
- 4a: spec :114-129 describes Postgres 13 -> 16; `infra/docker-compose.prod.yml:3` and `infra/docker-compose.dev.yml:3` are `postgres:13` (reverted in b8da60e). Diverges.
- Naming: `specs/2026-05-08-issue-53-dev-prod-workflow-analysis.md:11,88` and `plans/2026-05-08-issue-53-dev-prod-workflow.md:23,222` reference root `docker-compose.prod.yml`; files live in `infra/`.

## Why low, not medium
No runtime, security, or CI impact; nothing in code or CLAUDE.md references these files. Risk is only a future agent/human following 2b and reintroducing the env.bool bug.

## Better proposal
`git rm -r docs/superpowers/` (history keeps it). If kept, add one line at top of the audit spec: "1c/2b/3c amended in code; 4a reverted (b8da60e), still open." Don't edit checkboxes.

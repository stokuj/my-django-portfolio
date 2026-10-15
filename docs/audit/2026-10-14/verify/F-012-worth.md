# F-012 — No permissions block in CI workflow or deploy job (worth lens)

**Verdict:** CONFIRMED (fact), impact overstated
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- Fact holds: `.github/workflows/django.yml:1-46` has no `permissions:` key at workflow or job level; `docker-build-push.yml:82-86` (`deploy` job) has none either. Only `build-and-push` sets `contents: read` + `packages: write` (`docker-build-push.yml:26-28`).
- Risk premise ("may be write-all") does not hold today: `gh api repos/stokuj/my-django-portfolio/actions/permissions/workflow` returns `default_workflow_permissions: "read"`. So the token is already read-only in both workflows.
- `pull_request` runs from forks (`django.yml:6-7`) get a read-only token regardless of settings.
- `deploy` job never uses `GITHUB_TOKEN`; it only passes secrets to `appleboy/ssh-action` (`docker-build-push.yml:89-112`). `permissions: {}` there is pure hygiene.
- No git history or docs indicate a deliberate choice to omit permissions; adding them breaks nothing (`make verify` needs only checkout = `contents: read`).
- Still worth doing as defense-in-depth: pins intent in code so a future change of the repo/org default does not silently widen the token used by third-party code (`npm ci` `django.yml:37`, `uv sync` `django.yml:34`, unpinned actions). Cost: 2-4 lines.

## Better proposal
Smallest diff: add a top-level block to each workflow, rather than per-job edits:
- `django.yml`: top-level `permissions: { contents: read }`.
- `docker-build-push.yml`: top-level `permissions: {}`; `build-and-push` keeps its job-level override (`:26-28`), `deploy` inherits none.
Effort S. Severity low since the repo default is already `read`.

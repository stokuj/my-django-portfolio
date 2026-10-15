# F-012 - No permissions block in CI workflow or deploy job (reproduce lens)

**Verdict:** CONFIRMED (code fact), impact overstated
**Confidence:** high
**Adjusted severity:** low (hardening / defense in depth)

## Reasoning
- `.github/workflows/django.yml:1-46` has no `permissions:` key at top level or on job `test` (line 10). Confirmed.
- `.github/workflows/docker-build-push.yml:82-86` job `deploy` has no `permissions:`; no top-level block either (lines 1-12). Confirmed. `build-and-push` does scope itself (lines 26-28).
- Impact check: repo setting via `gh api repos/stokuj/my-django-portfolio/actions/permissions/workflow` returns `{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}`. So GITHUB_TOKEN in both jobs is currently read-only; the "may be write-all" path is not reachable today.
- `django.yml` triggers on `pull_request` (line 6); fork PRs get a read-only token regardless. Push-to-main runs use the repo default (read).
- `deploy` job never uses GITHUB_TOKEN; it only runs `appleboy/ssh-action` with secrets (lines 89-95). Explicit `permissions: {}` changes nothing functional.
- Residual risk: only if someone flips the repo default to write. Workflow-level pinning makes the files self-documenting and setting-independent.

## Better proposal
Same fix, low priority: top-level `permissions: contents: read` in `django.yml`; `permissions: {}` on `deploy` (or top-level `permissions: {}` in `docker-build-push.yml`, since `build-and-push` already declares its own). Effort S.

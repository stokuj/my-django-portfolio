# F-016 — Image build/push/deploy not gated on tests (worth lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning
- `.github/workflows/docker-build-push.yml:3-6` triggers on `push` to main/master (and `workflow_dispatch`); `build-and-push` (`:13`) has no `needs`, and `deploy` only has `needs: build-and-push` (`:84`). Nothing references Django CI.
- `.github/workflows/django.yml:3-7` runs `make verify` (`:45-46`) on push and pull_request to main as an independent workflow. On a push to main both run in parallel; a red verify does not stop deploy.
- Mitigation: PRs to main run Django CI (`django.yml:6-7`), so the gap only bites on direct pushes, merges with red/pending checks, or a test that fails only post-merge. Whether branch protection requires the check cannot be verified from the repo. Hence medium, not high.
- No doc or commit records a deliberate choice to keep deploy ungated (grep of docs/ and `git log -- .github/workflows`). The project treats `make verify` as "the single quality gate" (`docs/superpowers/specs/2026-05-08-issue-53-dev-prod-workflow-design.md:134`), so gating deploy is consistent with stated intent.

## Better proposal (smallest diff, no duplication)
Reuse the existing workflow instead of copying its steps or using `workflow_run`:
1. `django.yml`: add `workflow_call:` under `on:`.
2. `docker-build-push.yml`: add job `verify: uses: ./.github/workflows/django.yml` and `needs: verify` on `build-and-push`.

Avoid `workflow_run`: it runs in the default-branch context, `actions/checkout` would need `ref: ${{ github.event.workflow_run.head_sha }}`, it needs an explicit `conclusion == 'success'` check, and it drops the `workflow_dispatch` path. Note that with the proposal, push to main runs verify twice (once from Django CI's own `push` trigger); optionally drop `push` from `django.yml` to avoid this. Effort S.

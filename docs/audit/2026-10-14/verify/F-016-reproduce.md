# F-016 — Image build/push/deploy not gated on tests (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `.github/workflows/docker-build-push.yml:3-6` triggers on `push` to main/master and `workflow_dispatch`, independently of Django CI.
- `.github/workflows/docker-build-push.yml:13-80` (`build-and-push`) has no test step and no `needs:`; it only builds CSS, builds and pushes the image.
- `.github/workflows/docker-build-push.yml:84` — `deploy` has `needs: build-and-push` only. This is the only `needs:` in either workflow; no `workflow_run` anywhere.
- `.github/workflows/django.yml:3-7,45-46` runs `make verify` on push/PR to main as a separate workflow, so on a push to main both run in parallel and a failing verify does not stop the deploy.
- Mitigation not visible in code: if branch protection requires the PR check, broken code mostly cannot reach main via PR. It still deploys on direct pushes, on a verify that fails only post-merge, and on `workflow_dispatch` (line 6), which skips tests entirely.
- Minor: CLAUDE.md calls the file `django-ci.yml`; the real file is `django.yml`.

## Better proposal
Simplest: in `django.yml` add `workflow_call:` to `on:`, then in `docker-build-push.yml` add a job `verify: uses: ./.github/workflows/django.yml` and `needs: verify` on `build-and-push`. That reuses the existing job with no duplication. `workflow_run` also works, but it runs on the default-branch workflow definition and needs an explicit `conclusion == 'success'` check, so it is easier to get wrong.

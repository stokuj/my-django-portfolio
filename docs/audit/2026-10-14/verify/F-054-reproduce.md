# F-054 - No Dependabot config for GitHub Actions (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `.github/dependabot.yml` / `.yml` variants do not exist; `git ls-files .github` lists only `ISSUE_TEMPLATE/*` and `workflows/{django.yml,docker-build-push.yml}`. No `renovate.json` either.
- Pinned actions that would benefit, some already stale:
  - `.github/workflows/django.yml:18` `actions/checkout@v3` (v4 used elsewhere)
  - `.github/workflows/django.yml:26` `actions/setup-python@v4`
  - `.github/workflows/docker-build-push.yml:90` `appleboy/ssh-action@v1.0.3`
- Base images updated by hand only: `infra/Dockerfile:2` `node:22-slim`, `infra/Dockerfile:10` `python:3.13-slim`; compose images `postgres:13`, `redis:7-alpine`, `caddy:2` in `infra/docker-compose.{dev,prod}.yml`.
- Commit `ec37bac` ("patch Dependabot vulnerabilities") shows Dependabot *alerts* are on in repo settings, but alerts/security updates do not do routine version bumps; the claim "only updated by hand" holds for non-security updates.
- Minor inaccuracy: finding cites `line: 1` of a file that does not exist; fine for a missing-file finding.

## Better proposal
Add `.github/dependabot.yml` with weekly `github-actions` (directory `/`) and `docker` (directory `/infra`, not `/`, since the Dockerfile lives there). Optionally also `uv` (directory `/`) and `npm` (directory `/`), grouped, to cut PR noise. Effort S.

# sec-actions

Scope: `.github/workflows/django.yml`, `.github/workflows/docker-build-push.yml` at `dev` HEAD (4416049).

Verified OK: no `pull_request_target`; no `workflow_dispatch`/PR inputs interpolated into `run:`/`script:`; build job token scoped to `contents: read` + `packages: write`.

## 1. SSH deploy has no host key verification; GHCR PAT sent to whatever host answers
- Severity: medium | Category: security | Effort: S
- File: .github/workflows/docker-build-push.yml:89-103
- Problem: `appleboy/ssh-action` is called without `fingerprint:`, so the droplet host key is not checked. A spoofed host (DNS/route hijack of `SERVER_HOST`) would receive the full script, including the expanded `secrets.GHCR_PAT` on line 103.
- Proposal: add `fingerprint: ${{ secrets.SERVER_SSH_FINGERPRINT }}` (SHA256 of the droplet host key).
- Risk: wrong fingerprint blocks deploys until fixed; easy to verify with one manual run.

## 2. Third-party action holding the SSH key is pinned only to a mutable, old tag
- Severity: medium | Category: security | Effort: S
- File: .github/workflows/docker-build-push.yml:90 (also :32, :36, :70; django.yml:18, :20, :26)
- Problem: `appleboy/ssh-action@v1.0.3` receives `SSH_PRIVATE_KEY`, but a tag can be repointed by the upstream owner (tj-actions-style compromise). v1.0.3 is also several releases behind. All other actions are tag-pinned too.
- Proposal: pin at least `appleboy/ssh-action` (and ideally all actions) to a full commit SHA with a `# vX.Y.Z` comment; upgrade to current v1.x first.
- Risk: newer ssh-action versions changed some inputs (`script_stop` was replaced in v1.1+); check the script still fails fast.

## 3. CI uses deprecated action majors
- Severity: medium | Category: ci | Effort: S
- File: .github/workflows/django.yml:18, :26
- Problem: `actions/checkout@v3` and `actions/setup-python@v4` run on the Node 16 runtime, which GitHub has deprecated and force-migrates; the build workflow already uses `checkout@v4`, so the two workflows drift.
- Proposal: bump to `actions/checkout@v4`/`v5` and `actions/setup-python@v5`/`v6` (or `astral-sh/setup-uv`, since the job only installs uv).
- Risk: minimal.

## 4. Missing `permissions:` blocks on CI workflow and deploy job
- Severity: medium | Category: security | Effort: S
- File: .github/workflows/django.yml:9-10; .github/workflows/docker-build-push.yml:82-86
- Problem: neither declares `permissions`, so `GITHUB_TOKEN` gets the repo default (write-all if the repo/org setting is permissive). CI runs `npm ci` + `uv sync` (third-party code) with that token; deploy job never uses the token.
- Proposal: add top-level `permissions: contents: read` to django.yml and `permissions: {}` to the deploy job.
- Risk: none expected; neither job needs write scopes.

## 5. Long-lived GHCR PAT on the deploy path, interpolated into the script
- Severity: low | Category: security | Effort: S
- File: .github/workflows/docker-build-push.yml:103
- Problem: deploy logs in with a personal `GHCR_PAT` whose scope is not visible in the repo; it is templated with `${{ }}` straight into the remote script text (breaks on quotes, lands in the transferred script).
- Proposal: use a classic PAT limited to `read:packages` (or make the package public and drop the login); pass it via the action's `envs:` input and reference `$GHCR_PAT` in the script.
- Risk: none if scope is verified before rotating.

## 6. Any-branch `workflow_dispatch` overwrites the production `:latest` image
- Severity: medium | Category: bug | Effort: S
- File: .github/workflows/docker-build-push.yml:6, :13, :79-80; infra/docker-compose.prod.yml:37
- Problem: the deploy job is gated on main/master (line 86) but build-and-push is not. Dispatching on a feature branch pushes that build as `ghcr.io/stokuj/my-django-portfolio:latest`, the tag prod pulls. Any later manual `compose pull`/recreate on the droplet runs unreviewed code.
- Proposal: add the same `if:` ref guard to `build-and-push`, or restrict `workflow_dispatch` to main.
- Risk: none.

## 7. Deploy is not tied to the built commit; no concurrency guard; no rollback tag
- Severity: medium | Category: ops | Effort: M
- File: .github/workflows/docker-build-push.yml:99-112; infra/docker-compose.prod.yml:37,80,120
- Problem: server does `git pull` of current main and pulls `:latest`, not `github.sha`. With no `concurrency:` group, two quick merges can finish out of order and leave older code/image deployed. Only `:latest` is pushed and `docker image prune -af` (line 112) removes the previous image, so there is nothing to roll back to.
- Proposal: add `concurrency: { group: deploy-prod, cancel-in-progress: false }`; also tag images with `${{ github.sha }}` and `git checkout ${{ github.sha }}` on the server.
- Risk: SHA tagging needs compose `image:` to read a tag variable.

## 8. No Dependabot config for GitHub Actions
- Severity: low | Category: ci | Effort: S
- File: .github/ (no dependabot.yml)
- Problem: action versions (findings 2-3) are only updated by hand.
- Proposal: add `.github/dependabot.yml` with `package-ecosystem: github-actions` (weekly); it also keeps SHA pins current.
- Risk: PR noise.

## 9. CLAUDE.md names a workflow file that does not exist
- Severity: low | Category: docs | Effort: S
- File: CLAUDE.md:93
- Problem: references `django-ci.yml`; actual file is `.github/workflows/django.yml`.
- Proposal: fix the name.
- Risk: none.

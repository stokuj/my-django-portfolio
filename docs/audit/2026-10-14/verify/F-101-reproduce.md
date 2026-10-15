# F-101 (reproduce lens): Floating base image tags; app deployed only as :latest

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning (verified at HEAD)
- No digest pins anywhere:
  - `infra/Dockerfile:2` `FROM node:22-slim`, `infra/Dockerfile:10` `FROM python:3.13-slim`.
  - `infra/docker-compose.prod.yml:3` `postgres:13`, `:23` `redis:7-alpine`, `:154` `caddy:2` (same postgres/redis tags in `docker-compose.dev.yml:3,17`).
- App image is only `:latest`: hard-coded `ghcr.io/stokuj/my-django-portfolio:latest` at `infra/docker-compose.prod.yml:37,80,120`; CI builds/pushes it via `compose build web` / `compose push web` (`.github/workflows/docker-build-push.yml:77,80`). No SHA tag. `IMAGE_NAME` exported at :103 is unused by compose.
- Rollback is also lost locally: `docker image prune -af` (`docker-build-push.yml:113`) deletes the previous image on the droplet.
- Minor inaccuracy: `python:3.13-slim` is already minor-pinned; only node/caddy/redis/postgres float on a major tag.

## Caveats
- Rollback/SHA-tag half duplicates F-001; Dependabot half duplicates F-054. This finding adds only the base-image digest point.
- Digest pinning without Dependabot (F-054) would freeze base images and stop picking up security patches on rebuild; the floating `-slim` tags currently get them for free. Pinning is only a net win together with automated bumps.
- Not exploitable by itself; reproducibility/supply-chain hygiene. Low is right.

## Better proposal
Merge into F-001 (SHA tag) + F-054 (Dependabot `docker` ecosystem for `/infra`). Pin digests (`image:tag@sha256:...`) only once Dependabot is in place to bump them; otherwise keep major/minor tags.

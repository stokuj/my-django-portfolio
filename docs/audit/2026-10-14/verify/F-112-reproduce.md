# F-112 — IMAGE_NAME in .env.example is unused (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `.env.example:30` sets `IMAGE_NAME=name_of_image` under "# Docker configuration".
- Repo-wide grep (excluding lockfiles/audit docs) finds no `${IMAGE_NAME}` interpolation anywhere. Prod compose hardcodes `image: ghcr.io/stokuj/my-django-portfolio:latest` at `infra/docker-compose.prod.yml:37,80,120`; dev compose hardcodes `my-django-portfolio:dev` (`infra/docker-compose.dev.yml:26,62,97`).
- Makefile and `django/config/` do not reference it.
- Workflow defines its own value (`.github/workflows/docker-build-push.yml:10,52`) and the deploy script does `export IMAGE_NAME=...` (`:105`) before `docker compose --env-file .env ... -f infra/docker-compose.prod.yml` (`:107-109`), but the compose file never interpolates it, so neither the export nor the `.env` value has any effect.
- Side note: `env_file:` in compose (`infra/docker-compose.prod.yml:39,83,123`) injects it into container env, but no code reads it.

## Better proposal
Delete `.env.example:30` (and the "# Docker configuration" header if left empty). Parameterising the compose image is optional; if done, remove the dead `export` at `docker-build-push.yml:105` together (F-055 overlap). Effort S.

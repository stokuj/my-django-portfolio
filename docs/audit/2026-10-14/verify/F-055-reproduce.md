# F-055 (reproduce): Build workflow duplication: job env, dead IMAGE_NAME, preflight CSS, master fallbacks

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning
- **Job env vs .env heredoc.** The job env at `.github/workflows/docker-build-push.yml:16-25` only holds values that the heredoc at `:47-66` also writes, with the same values. The compose file `infra/docker-compose.prod.yml` interpolates `${SECRET_KEY}`, `${DOCKER_DB_*}` and so on (`:7-9`, `:53-62`), and `--env-file .env` (`:77`, `:80`) already supplies all of them. So the job env is redundant. The heredoc itself must stay: `env_file: ../.env` (`infra/docker-compose.prod.yml:39-40`) needs the file to exist, and it also carries vars the job env lacks (CSRF_TRUSTED_ORIGINS, PORTFOLIO_*, APP_DOMAIN).
- **IMAGE_NAME is dead.** It is set at `docker-build-push.yml:10`, `:52` and `:105`, and in `.env.example:30`. The prod compose file hardcodes `image: ghcr.io/stokuj/my-django-portfolio:latest` (`infra/docker-compose.prod.yml:37,80,120`). Nothing in the repo reads `${IMAGE_NAME}`; grep finds only these definitions.
- **Preflight CSS duplicates the Dockerfile.** `docker-build-push.yml:34-43` (setup-node with Node 20, `npm ci`, `build:css:prod`) repeats the `css-builder` stage in `infra/Dockerfile:2-7` (Node 22). The image takes its CSS from that stage (`infra/Dockerfile:23`), so the runner's output is thrown away. A CSS failure would also fail the docker build, so the step adds no extra check.
- **master fallbacks.** These are at `:86` and `:100-101`, plus the `master` trigger at `:5`, which the finding does not list. The remote has only `refs/heads/main` (`git ls-remote`). They do nothing, and they cause no harm.
- **Tests.** `tests/test_operational_files.py:79-95` checks only the down/up/prune lines, so the proposed deletions break no test.

## Better proposal
- Apply the finding's proposal.
- Keep the `.env` heredoc and drop `IMAGE_NAME=` from it.
- Also remove `master` from the trigger at `:5` (and optionally `.github/workflows/django.yml:5,7`).
- Remove the `setup-node` step together with the preflight step.
- Effort: S.

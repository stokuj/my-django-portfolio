# F-055 (reproduce lens): Build workflow duplication: job env, dead IMAGE_NAME, preflight CSS, master fallbacks

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning
- **Job env duplicates the .env heredoc.** `.github/workflows/docker-build-push.yml:16-25` sets SECRET_KEY, DJANGO_DEBUG, ALLOWED_HOSTS and DOCKER_DB_*. The same values appear in the heredoc at `:47-66`, which also has CSRF_TRUSTED_ORIGINS and APP_DOMAIN. Every `${...}` in `infra/docker-compose.prod.yml` (7-9, 53-62, 92-101, 130-139, 156-169) resolves from `--env-file .env` (`:77`, `:80`), or has a default. No `run` step reads the job env directly. The two sets of values are identical, so the precedence between shell env and the env file does not matter.
- **IMAGE_NAME is dead.** It is set at `:10`, `:52` and `:105`, and in `.env.example:30`. Every app service in compose hardcodes `image: ghcr.io/stokuj/my-django-portfolio:latest` (`infra/docker-compose.prod.yml:37,80,120`). A grep for IMAGE_NAME finds no reader in compose, `infra/`, the Makefile, Python or shell files.
- **Preflight CSS is redundant.** `:40-43` runs `npm ci && npm run build:css:prod`. `infra/Dockerfile:2-7` runs the same commands in its `css-builder` stage, and `:23` copies that stage's style.css over whatever was in the build context. The preflight output is therefore overwritten and never used. The only thing it adds is an earlier failure, and the Docker build fails on the same error anyway.
- **master fallbacks are dead.** `git ls-remote --heads origin` lists only `main` and `audit/codebase-2026-05`. The references at `:86` and `:100-101` are unreachable fallbacks.
- **Tests are not affected.** `tests/test_operational_files.py:79-95` only checks `down --remove-orphans`, the prune commands and their order. None of those are touched by the proposal.

## Imprecisions in the finding (not refuting)
- `master` also appears in the trigger at `:5` (`branches: [ "main", "master" ]`). The finding leaves it out.
- The preflight block is the `Set up Node.js` step at `:34-38` plus the `Build CSS (preflight)` step at `:40-43`. Both can go.

## Better proposal
In one PR:
- Delete the job `env` (`:16-25`).
- Delete the `Set up Node.js` and `Build CSS (preflight)` steps (`:34-43`).
- Remove IMAGE_NAME from `:10`, `:52`, `:105` and `.env.example:30`.
- Drop `master` from `:5`, `:86`, `:100` and `:101`.

Effort is S. Run `uv run python -m pytest tests/` afterwards.

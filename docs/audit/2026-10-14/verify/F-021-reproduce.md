# F-021 — Placeholder SECRET_KEY / DEBUG=True never caught; check --deploy not run

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged; conditional on operator error, no evidence the live droplet .env is misconfigured)

## Reasoning
- `django/config/settings.py:35-37` rejects only an empty `SECRET_KEY`; `:40` takes `DJANGO_DEBUG` as-is. No length/placeholder check.
- `.env.example:2` ships `DJANGO_DEBUG=True`, `:5` ships `SECRET_KEY=your_generated_secure_key_here` (30 chars).
- `Makefile:7` (`dev-up`) -> `infra/scripts/ensure_env.py` copies the example to `.env` in dev mode only (prod mode refuses to create it). `README.md:114` tells users to `cp .env.example .env`.
- `Makefile:36` runs plain `manage.py check` with `DJANGO_DEBUG=True`; no `--deploy` anywhere in repo (grep).
- Deploy: `.github/workflows/docker-build-push.yml:107-109` does pull / down / up with no check; web container command (`infra/docker-compose.prod.yml:43-46`) is migrate + collectstatic + gunicorn, no check.
- With `DEBUG=True`, the `if not DEBUG:` block (`settings.py:98-105`) is skipped, so HSTS/SSL redirect/secure cookies are also off.
- Reproduced locally: `check --deploy` with the example values reports W004, W008, W009, W012, W016, W018. With a strong key + `DJANGO_DEBUG=False` + real host it reports "no issues", so `--fail-level WARNING` would not break a correctly configured prod.

## Better proposal
Run the check after `pull` and BEFORE `down` (line 108), so a failure leaves the old stack running, and skip the DB wait / deps:

    docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml \
      run --rm --no-deps --entrypoint "" web python manage.py check --deploy --fail-level WARNING

`script_stop: true` (line 95) already aborts the script on non-zero exit.

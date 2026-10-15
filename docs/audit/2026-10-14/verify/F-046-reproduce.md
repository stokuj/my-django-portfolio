# F-046 — Runtime user owns the application code (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `infra/Dockerfile:33-36` runs `chown -R app:app /app /home/app` after source is copied (`:22-23`), then `USER 10001:10001` (`:42`). All of `/app/django` (Python source, templates, settings, `entrypoints/wait-for-db.sh`) is writable by the runtime uid.
- Prod compose does not bind-mount code; only `staticfiles_volume`, `media_volume` (`infra/docker-compose.prod.yml:47-51, 89-90`) and `celerybeat_schedule` (`:127-128`). So the code lives in the image layer, owned by uid 10001.
- No `read_only`, `cap_drop` or `security_opt` anywhere in `infra/docker-compose.prod.yml` or `infra/docker-compose.dev.yml` (grep returned nothing).
- Installed packages go to system site-packages as root (`Dockerfile:27`), so those are not writable; only `/app` is.

## Limits of the claim
- Requires an existing RCE first; this is defense-in-depth, not an exploitable path on its own.
- "Persist" is bounded: edits survive process/container restarts (`restart: always`, prod compose `:4,24,82,122`), but every deploy runs `down` + `up -d --force-recreate` (`.github/workflows/docker-build-push.yml:108-109`), which discards the container writable layer. Gunicorn has no `--reload` (`prod.yml:46`), so rewritten code runs only after a restart.
- An attacker with RCE as uid 10001 can already read `SECRET_KEY`/DB creds from env, so code-tamper adds little marginal impact. Hence low.

## Better proposal
- Keep image-time ownership needed for named-volume init: `mkdir -p /app/staticfiles /app/media /app/django/celerybeat-schedule && chown app:app /app/staticfiles /app/media /app/django/celerybeat-schedule /home/app` (non-recursive on `/app`). Named volumes copy ownership from these image dirs on first creation, so collectstatic, media writes and beat still work.
- Optional compose hardening on web/worker/beat: `security_opt: ["no-new-privileges:true"]`, `cap_drop: [ALL]`. Skip `read_only: true` unless `/tmp` is given a tmpfs (gunicorn worker heartbeat uses tmp files).
- Missing `__pycache__` write access is harmless (Python just skips writing .pyc).

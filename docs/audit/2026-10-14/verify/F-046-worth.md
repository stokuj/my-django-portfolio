# F-046 — Runtime user owns the application code (worth lens)

**Verdict:** CONFIRMED (severity lowered)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `infra/Dockerfile:33-36` runs `chown -R app:app /app /home/app`, then `USER 10001:10001` (42). All of `/app/django` (code, settings, templates, entrypoint) is writable by the runtime user.
- Only three paths need runtime writes: `/app/staticfiles` (collectstatic, `infra/docker-compose.prod.yml:45,49`; `STATIC_ROOT` at `django/config/settings.py:157`), `/app/media` (`settings.py:178`, prod compose 51/90), `/app/django/celerybeat-schedule` (prod compose 126-128). No other runtime writes found under `/app/django` (only file I/O in `django/main/*.py` is a read at `views.py:346`).
- No deliberate decision: commit 512ceef says "make runtime dirs writable"; the blanket `/app` chown is an over-reach of that intent. No test asserts it (`tests/test_operational_files.py` checks only the `dockerfile:` line).
- Compose services have no `read_only`, `cap_drop` or `security_opt` (prod compose 33-151). Confirmed.
- Why lowered to low: there are no bind mounts, so rewritten code lives only in the container layer and is wiped on redeploy (image recreate). An attacker with RCE already holds `SECRET_KEY` and DB credentials from env (prod compose 52-64). This is defense in depth, not an exploitable gap on its own.
- Named volumes copy ownership from the image dir on first creation; keeping the three dirs chowned preserves that. Existing volumes are unaffected.

## Better proposal (smallest diff)
Replace `/app` with the three runtime dirs on line 36:

    chown -R app:app /app/staticfiles /app/media /app/django/celerybeat-schedule /home/app

Python will fail silently to write `__pycache__` (harmless). Skip `cap_drop`/`no-new-privileges` unless wanted; if added, `security_opt: [no-new-privileges:true]` is a safe one-liner per service. Verify with `make dev-up` that collectstatic and beat still start.

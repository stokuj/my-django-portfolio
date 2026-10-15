# F-129 - Service list describes prod only (reproduce)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `docs/architecture.md:6-13` says the "core runtime services are orchestrated with Docker Compose" and lists `web` as "Django app served by Gunicorn" and `caddy` as a service. It gives no dev/prod split. `grep -i "dev\|prod"` over the file finds no matches.
- `infra/docker-compose.dev.yml:32-36`: dev `web` runs `python manage.py runserver 0.0.0.0:8000` and publishes `127.0.0.1:8000:8000`. The dev compose file has no `caddy` service (grep finds nothing).
- `infra/docker-compose.prod.yml:46` starts `gunicorn config.wsgi:application`. `infra/docker-compose.prod.yml:153` defines `caddy`.
- The request-flow section (`docs/architecture.md:133-138`) and the static/media section (`:182-183`) are also prod-only, because they route everything through Caddy.
- The project CLAUDE.md already says "Dev compose omits Caddy". Only the human docs leave this out.

## Better proposal
Same fix, scoped to prod. Change line 6 to say "In production (`infra/docker-compose.prod.yml`)". Add one line saying that dev compose (`infra/docker-compose.dev.yml`) has no Caddy and runs `web` with `runserver` on 127.0.0.1:8000.

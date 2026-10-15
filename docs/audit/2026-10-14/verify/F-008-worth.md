# F-008 — web and caddy have no restart policy in prod (worth lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** high (unchanged)

## Reasoning
- `infra/docker-compose.prod.yml`: `restart: always` on db (:4), redis (:24), worker (:82), beat (:122). `web` (:33-74) and `caddy` (:153-178) have no `restart:` key, so they default to `no`.
- After a host reboot or dockerd restart, db/redis/worker/beat come back but web and caddy stay down. The site is offline until someone redeploys. Deploys run `down` + `up -d --force-recreate` (`.github/workflows/docker-build-push.yml:108-109`), so only a deploy brings them back.
- I found no deliberate decision against it. In git history, `restart: always` was only ever added to services (commits c2d9dec, 335e524, 6e39938, 4c643b5) and was never removed from web or caddy. The dev compose sets `restart: unless-stopped` on its services (`infra/docker-compose.dev.yml:4,18,64,99`).
- The fix is safe. On restart, web reruns `migrate` and `collectstatic` (:43-46), and both are idempotent.

## Better proposal
The proposal is already the smallest fix: add `restart: always` to `web` and `caddy`, which matches the other prod services.
Optional follow-up: add one assertion to `tests/test_operational_files.py`, next to the existing `logging:` count test at :70-72, for example `assertEqual(content.count("    restart: always"), 6)`. That stops the gap from coming back.

# F-015 (reproduce lens): workflow_dispatch from any branch overwrites production :latest image

**Verdict:** CONFIRMED (mechanism), severity overstated
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `.github/workflows/docker-build-push.yml:6`: `workflow_dispatch:` has no branch filter, so it can run from any ref.
- `build-and-push` (lines 13-80) has no `if:`; it checks out the dispatched ref (line 32), builds (line 77) and pushes `web` (line 80).
- The pushed tag is hard-coded in `infra/docker-compose.prod.yml:37,80,120` (`ghcr.io/stokuj/my-django-portfolio:latest`), not `${IMAGE_NAME}`. The finding cites `docker-compose.prod.yml`; the real path is `infra/docker-compose.prod.yml`.
- Only `deploy` is gated (line 86), so a feature-branch dispatch overwrites `:latest` in GHCR without deploying.

## Why the severity drops
- Only users with write access can trigger `workflow_dispatch`. This is a single-owner repo, so the only person who can do it is the owner, by hand. It is not exploitable by outsiders.
- Prod does not pick it up on its own. The server pulls only inside the deploy script (line 107), and every main deploy rebuilds and pushes `:latest` from main first (`needs: build-and-push`, line 84). Nothing auto-pulls: grep finds no watchtower in the compose file.
- The real exposure is narrow: (a) a manual `docker compose pull` on the server after a feature dispatch, or (b) a race with no `concurrency:` group, where a feature dispatch pushes between a main run's push and its deploy pull.

## Better proposal
Same S-effort fix: add `if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'` to `build-and-push`, matching line 86. Or drop `workflow_dispatch` if it is not needed. Optionally add `concurrency: deploy-prod` to rule out the race.

# F-103 — Prod Postgres published on host loopback (reproduce lens)

**Verdict:** CONFIRMED (with corrections)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `infra/docker-compose.prod.yml:10-11` publishes `"127.0.0.1:15432:5432"` on the `db` service. Present at HEAD.
- The app does not need it: `web`, `worker`, `beat` connect over the compose network via `DB_HOST=${DOCKER_DB_HOST}` / `DB_PORT=${DOCKER_DB_PORT}` (`infra/docker-compose.prod.yml:61-62, 100-101, 138-139`), with `.env.example:38-39` setting `DOCKER_DB_HOST=db`, `DOCKER_DB_PORT=5432`.
- No repo code, script, or test uses port 15432 in prod. Only `Makefile:12` (dev URLs) and `infra/docker-compose.dev.yml:10` reference it.
- Correction: the claim "copied from dev" is wrong. Git history shows the mapping came from the original prod `docker-compose.yml` (commit `1c5b232`), and the plan `docs/superpowers/plans/2026-05-08-issue-53-dev-prod-workflow.md` moved prod over unchanged. Dev copied it from prod, not the other way around.
- Real exposure is small. The port is bound to loopback only, so it is not reachable from the internet. A local process still needs the DB password (`POSTGRES_PASSWORD`, line 9), and anyone with a shell on the droplet who can read `../.env` already has that password. This is defense in depth, not an exploitable path.

## Better proposal
Remove `ports:` (lines 10-11) from the prod `db` service. For manual access, use `docker compose -f infra/docker-compose.prod.yml exec db psql -U "$DOCKER_DB_USER" "$DOCKER_DB_NAME"`. Before removing it, check that the operator has no SSH-tunnel or DB GUI workflow that uses 15432 on the droplet; no such workflow is documented in the repo. Effort: S.

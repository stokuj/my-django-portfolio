# F-104: Single explicit bridge network: redundant and flat

- Lens: reproduce
- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low

## Reasoning

- `infra/docker-compose.prod.yml:180-182` declares a single network, `app-network` (`driver: bridge`). All six services join it: db `:14-15`, redis `:25-26`, web `:68-69`, worker `:108-109`, beat `:145-146`, caddy `:172-173`. The compose default network is also one bridge network that every service joins, so this block adds nothing except a different network name.
- The network is flat. Caddy publishes ports 80 and 443 (`:155-157`) and only needs `web:8000` (`infra/Caddyfile:29`). It can still reach `db:5432` and `redis:6379`.
- Redis (`:22-31`) has no `command`/`requirepass`, so anyone on the network can use it without auth. Postgres needs a password (`:6-9`). Neither publishes a port to the outside: db is bound to `127.0.0.1:15432` only (`:10-11`), and redis publishes no ports.
- How it could be exploited: only if Caddy itself were compromised (RCE in the upstream `caddy:2` image). Nothing reaches redis or db directly from the internet. That makes this defense in depth, not an exposed hole, so low is the right severity.
- The stated risk (network rename recreates the stack) does not matter in practice. The deploy already runs `down --remove-orphans` and `up -d --force-recreate` on every release (`.github/workflows/docker-build-push.yml:108-109`), and the project name stays `my_django_portfolio` (`Makefile:4`). Volumes are not affected.

## Better proposal

Delete the top-level `networks:` block and every per-service `networks: [app-network]` key (about 14 lines). Same behaviour, less YAML. Network segmentation for Caddy is optional. If it is wanted, a cheaper defense-in-depth step is a Redis password (`--requirepass` plus a `redis://:pass@redis` broker URL).

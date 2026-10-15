# F-100 - Duplicate static/media file_server blocks (reproduce)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (simplification, cosmetic)

## Reasoning
- `infra/Caddyfile:18-21` (`handle /static/*`) and `infra/Caddyfile:23-26` (`handle /media/*`) have identical bodies: `root * /srv` + `file_server`.
- Indentation in the apex site block (`infra/Caddyfile:17-29`) is 1 space at block level / 5 spaces inside, while the rest of the file (`:2`, `:7`, `:12`) uses 4 spaces. Confirmed inconsistent.
- No functional bug: `file_server` is terminal, so `reverse_proxy web:8000` (`:29`) is not reached for `/static/*` and `/media/*`.
- No test or tooling parses these blocks (only mount at `infra/docker-compose.prod.yml:159`), so the change is safe to make.

## Proposal (refined)
Inline `handle` matchers take only one path, so a named matcher is required:

```
https://{$APP_DOMAIN} {
    @files path /static/* /media/*
    handle @files {
        root * /srv
        file_server
    }

    reverse_proxy web:8000
}
```

Do not drop the `handle` wrapper: with bare `file_server @files`, Caddy's default directive order puts `reverse_proxy` before `file_server`, so Django would serve everything. Run `caddy validate` / `caddy fmt` after editing (`caddy fmt` also fixes indentation).

Effort: S. Risk: none if validated.

# F-015 — workflow_dispatch from any branch overwrites production :latest image (worth lens)

**Verdict:** CONFIRMED (fix worth doing, severity lowered)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `.github/workflows/docker-build-push.yml:6` enables `workflow_dispatch` with no branch filter; `build-and-push` (lines 13-80) has no `if:`. Only `deploy` is gated (line 86).
- The pushed tag is fixed: `infra/docker-compose.prod.yml:37,80,120` hardcode `ghcr.io/stokuj/my-django-portfolio:latest` (finding cites the path without the `infra/` prefix). A dispatch on `dev` therefore overwrites `:latest` in GHCR.
- Impact is narrower than stated: `workflow_dispatch` requires repo write access (single-maintainer repo), and prod only picks up the bad image on a manual `docker compose pull` on the droplet before the next main deploy (line 107 runs only from `deploy`, which is skipped off main). The next push to main rebuilds and overwrites `:latest`. Not exploitable by outsiders, so medium overstates it; it is a self-inflicted foot-gun.
- No doc or commit records a deliberate choice to build non-main branches from dispatch (`git log` on the workflow, `docs/`).
- Proposal is correct and safe: skipping `build-and-push` also skips `deploy` via `needs`, which is already the behavior off main.

## Better proposal
Smallest diff: copy the existing guard from line 86 onto `build-and-push`:
`if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'`
(keep `master` for consistency with lines 5 and 86). SHA tagging for non-main builds is more work and not needed (YAGNI) unless branch images are actually wanted.

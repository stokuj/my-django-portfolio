# F-056 - Long-lived GHCR PAT pasted into the remote script (reproduce lens)

**Verdict:** PARTIALLY CONFIRMED. The code matches; most of the claimed impact does not hold up.
**Confidence:** high
**Adjusted severity:** low

## What holds
- `.github/workflows/docker-build-push.yml:103`: `echo "${{ secrets.GHCR_PAT }}" | docker login ghcr.io -u "${{ secrets.GHCR_USERNAME }}" --password-stdin` sits inside the `appleboy/ssh-action@v1.0.3` `script:` block (lines 89-112), so the secret is expanded into the script text before it is sent.
- The PAT's scope and lifetime are not visible from the repo. `GHCR_PAT` is used only on line 103.

## What does not hold
- **"Breaks on quotes":** GitHub PATs (`ghp_...`, `github_pat_...`) contain only `[A-Za-z0-9_]`, so a quote cannot appear and the line cannot break. The secret is also not attacker-controlled, because the job runs only on push to main/master or on workflow_dispatch (lines 3-6, 86). That rules out script injection.
- **"Sent as part of the script":** the proposed `envs:` fix does not change this. `appleboy/ssh-action` (drone-ssh) applies `envs` by prepending `export VAR='value'` lines to the same script it sends over SSH, so the token still travels inside the script. The real gain is shell-safe quoting, which matters little for a PAT charset. Either way the token stays on the server: `docker login` writes it to `~/.docker/config.json` on the droplet in base64 (effectively plaintext).
- GitHub log masking applies to the expanded secret, so it does not leak into the Actions log.

## Better proposal
The real risk is a long-lived credential stored on the droplet, not how it is passed. Pick one:
1. Make the GHCR package public and remove line 103 (no credential at all), or
2. Use a short-lived token: add `permissions: { contents: read, packages: read }` to the `deploy` job (it has no `permissions` block today; see lines 82-87), log in with `${{ secrets.GITHUB_TOKEN }}` / `${{ github.actor }}`, and run `docker logout ghcr.io` after `pull` (line 107). Then nothing long-lived is sent or left on disk. Moving to `envs:` is optional.
3. If the PAT stays, it should be a fine-grained or classic PAT with only `read:packages` and an expiry. That has to be checked in GitHub settings, not in the repo.

Effort: S.

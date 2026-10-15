# F-017 — SSH deploy has no host key verification (worth lens)

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low (was medium)

## Reasoning
- `.github/workflows/docker-build-push.yml:89-95`: `appleboy/ssh-action@v1.0.3` gets `host`, `username`, `key`, `script_stop` only; no `fingerprint:` input. Without it the action skips host key checking, so any host answering for `SERVER_HOST` is trusted.
- `:103`: `${{ secrets.GHCR_PAT }}` is expanded by Actions into the script text before it is sent, so a spoofed host receives the PAT in clear. `:105` also sends repo name (not secret).
- Pubkey auth itself is not replayable by a MITM, so `SSH_PRIVATE_KEY` is not leaked; the exposure is the PAT plus the attacker being treated as the deploy target.
- No doc or commit records a deliberate choice to skip verification (`git log` on the workflow, grep of docs/ for fingerprint/known_hosts: nothing).
- Severity lowered: exploitation needs an active network position or DNS hijack between a GitHub-hosted runner and the droplet. Real, but not a likely path. Fix is still worth it: one line, built-in action input, no new dependency.

## Better proposal
Same as proposed, one line in the `with:` block:
`fingerprint: ${{ secrets.SERVER_SSH_FINGERPRINT }}`
Value = SHA256 of the droplet host key, e.g. `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub | awk '{print $2}'` run on the server (not from `ssh-keyscan` over the network, which would defeat the point).
Risk noted in the finding holds: a host key rotation or droplet rebuild breaks deploys until the secret is updated.

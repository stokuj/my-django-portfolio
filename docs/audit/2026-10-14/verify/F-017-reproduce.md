# F-017 - SSH deploy has no host key verification

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning
- `.github/workflows/docker-build-push.yml:89-95`: the `deploy` job calls `appleboy/ssh-action@v1.0.3` with `host`, `username`, `key` and `script_stop` only. It does not set `fingerprint`, and no other step pins a known_hosts entry.
- In appleboy/ssh-action (built on drone-ssh/easyssh-proxy), an empty `fingerprint` makes the client use `ssh.InsecureIgnoreHostKey()`, so it accepts any host key.
- `:103`: `${{ secrets.GHCR_PAT }}` and `${{ secrets.GHCR_USERNAME }}` are expressions, and Actions expands them before the action runs. The script sent over SSH therefore carries the PAT in plaintext. A host that impersonates SERVER_HOST would receive it, and log masking does not help here.
- Reachability: the attacker needs a MITM position between the GitHub runner and the droplet, or control of DNS if SERVER_HOST is a hostname. That is not trivial, so medium (not high) fits. Public-key auth does not leak the private key to a spoofed host. What leaks is the GHCR_PAT, and the impostor could also feed fake deploy output to the job.

## Better proposal
- Add `fingerprint: ${{ secrets.SERVER_SSH_FINGERPRINT }}` (SHA256 of the droplet host key, from `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`). Effort S.
- Optional, same edit: pass the PAT through `envs:` instead of inlining `${{ }}` into the script. Also scope GHCR_PAT to `read:packages` only.

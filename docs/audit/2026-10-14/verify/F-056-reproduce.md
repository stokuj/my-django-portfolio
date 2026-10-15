# F-056 (reproduce): Long-lived GHCR PAT pasted into the remote script

**Verdict:** CONFIRMED (partly overstated)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `.github/workflows/docker-build-push.yml:103`: `echo "${{ secrets.GHCR_PAT }}" | docker login ghcr.io -u "${{ secrets.GHCR_USERNAME }}" --password-stdin` sits inside the `script:` of `appleboy/ssh-action@v1.0.3` (`:90`, `:96`). Actions substitutes the secret before the step runs, so the plaintext token is part of the script sent over SSH and run by the remote shell. Confirmed.
- This is the only use of `GHCR_PAT` in the repo. Its scope and lifetime cannot be seen from the repo; "long-lived" is an assumption.
- Overstated: "breaks on quotes". GitHub PATs (`ghp_`/`github_pat_` plus `[A-Za-z0-9_]`) never contain quotes or `$`, so the quoting does not break in practice. Only a malformed secret would break it.
- Not reachable by an attacker: the step runs only on push to main/master (`:86`), there is no untrusted input in the script, and the runner masks the secret in logs. The only exposure is on the droplet itself. While the script runs, the shell command line can be read by root and the same user, and `docker login` stores the token in `~/.docker/config.json` anyway. So the risk is low.
- Proposed fix is weak: in appleboy/ssh-action (drone-ssh), `envs:` works by adding `export VAR="value"` lines to the front of the same remote script. Moving the token to `envs:` does not keep it out of the script text. It only fixes quoting, which is not a real problem here.

## Better proposal
- Drop the PAT: in the deploy job, set `permissions: { contents: read, packages: read }` and pass `${{ secrets.GITHUB_TOKEN }}` with `-u ${{ github.actor }}`. The token expires when the job ends, and the pull at `:107` runs inside the job. Then delete the `GHCR_PAT`/`GHCR_USERNAME` secrets. Another option is to make the GHCR package public and remove the login.
- If the PAT stays, make it a fine-grained or classic token with only `read:packages` and an expiry date.
- Effort: S.

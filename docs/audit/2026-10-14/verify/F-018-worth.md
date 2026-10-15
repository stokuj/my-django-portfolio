# F-018 (worth): Third-party ssh-action holding the SSH key is pinned to a mutable, old tag

- **Verdict:** CONFIRMED
- **Confidence:** high
- **Adjusted severity:** medium (unchanged)

## Reasoning
- `.github/workflows/docker-build-push.yml:90` uses `appleboy/ssh-action@v1.0.3`, which is a tag, not a SHA. It receives `secrets.SSH_PRIVATE_KEY` (`:94`), and `secrets.GHCR_PAT` is interpolated into its `script` input (`:103`). A moved tag would run attacker code holding prod SSH and GHCR credentials. The claim holds.
- Other refs are tag-only too: `actions/checkout@v4` (`:32`), `actions/setup-node@v4` (`:35`), `docker/login-action@v3` (`:70`), and `.github/workflows/django.yml:18,20,26`. These are first-party or verified publishers and see no deploy secrets, so they carry less risk.
- I found no deliberate decision against pinning: `docs/` (outside `docs/audit`) never mentions ssh-action, SHA pinning or Dependabot, and the git log for the workflow shows none.
- There is no `.github/dependabot.yml`. SHA pins without it go stale silently, and the finding does not mention this.
- The upgrade risk is real. `script_stop: true` (`:95`) is gone in later v1.x, so if you bump the version, add `set -e` as the first line of `script` (`:97`). Otherwise a failed `git pull` or `docker login` still leads to `down` + `up` with a stale or missing image.

## Better proposal (smallest diff)
1. Pin only `appleboy/ssh-action` to a full commit SHA with a `# vX.Y.Z` comment. If you upgrade, add `set -e` at the top of `script` and drop `script_stop`.
2. Add a minimal `.github/dependabot.yml` with `package-ecosystem: github-actions`, so pins (SHA + comment) get bumped automatically.
3. Optional: SHA-pin the first-party actions as well. They are low value compared with the SSH action.
4. Optional alternative: replace the action with a plain `run: ssh ...` step (key in `~/.ssh`, host key in `known_hosts`). This removes the third-party dependency and also adds host-key verification. The action has no `fingerprint` set, so the host key is not verified today.

Effort: S.

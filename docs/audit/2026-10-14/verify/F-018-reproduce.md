# F-018 - Third-party ssh-action holding the SSH key is pinned to a mutable, old tag

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning
- `.github/workflows/docker-build-push.yml:90` - `uses: appleboy/ssh-action@v1.0.3`, a tag, not a commit SHA.
- The action receives `key: ${{ secrets.SSH_PRIVATE_KEY }}` (`:94`). `secrets.GHCR_PAT` is expanded into `script` (`:103`), so the action gets it as plain text input too. Code behind a moved tag could steal both and get shell access on the production droplet.
- Every other action is pinned by tag only as well: `docker-build-push.yml:32,35,70` and `django.yml:18,20,26`. `django.yml` still uses the older `actions/checkout@v3` and `actions/setup-python@v4`.
- Reachability: the deploy job runs only on pushes to main/master (`:86`), so a moved tag is the only way in. This is a supply-chain risk, not an exploit reachable from a PR. The tj-actions incident shows it happens. Medium fits.
- I did not check upstream that v1.0.3 is behind v1.2.x (no network). That detail is secondary.

## Better proposal
Pin all actions in both workflows to full commit SHAs with a `# vX.Y.Z` comment, and let Dependabot (`github-actions` ecosystem) bump them. When upgrading ssh-action past v1.0.x, `script_stop` (`:95`) is no longer supported. Add `set -e` at the top of `script` so the deploy still aborts on the first failing command.

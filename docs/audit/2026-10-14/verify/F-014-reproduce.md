# F-014 (reproduce) - CI builds CSS on EOL Node 20 while the image uses Node 22

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `.github/workflows/django.yml:20-22` uses `actions/setup-node@v4` with `node-version: 20`; `npm ci` follows at :37 and `make verify` (which builds CSS) at :45.
- `.github/workflows/docker-build-push.yml:35-37` uses `node-version: 20`; the "Build CSS (preflight)" step at :39-42 runs `npm run build:css:prod` on it.
- `infra/Dockerfile:2` builds the shipped CSS in `FROM node:22-slim AS css-builder` (:2-7).
- No `.nvmrc`/`.node-version` in repo root, no `engines` in `package.json`, so nothing pins one version.
- Node 20 EOL was 2026-04-30; today is 2026-10-15, so CI runs on an unsupported runtime.

The mismatch exists exactly as described. Severity lowered: the CSS that ships is built inside the image on Node 22 (Dockerfile:2-7), so the CI Node 20 build is only a preflight check. A Tailwind build differing between Node 20 and 22 is unlikely, and no failure is observed. It is a hygiene/drift issue, not a "should fix" bug.

Side note: CLAUDE.md calls the workflow `django-ci.yml`; the file is `.github/workflows/django.yml`.

## Better proposal
Simplest: change `node-version: 20` to `22` in `django.yml:22` and `docker-build-push.yml:37` (two one-line edits). Adding `.nvmrc` + `node-version-file: .nvmrc` is fine too, but the Dockerfile tag still has to be kept in sync by hand, so it does not remove the drift risk.

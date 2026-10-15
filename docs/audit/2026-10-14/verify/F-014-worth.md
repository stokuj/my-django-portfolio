# F-014 (worth): CI builds CSS on EOL Node 20 while the image uses Node 22

**Verdict:** CONFIRMED (the problem is real; the proposed fix is not the simplest one)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `.github/workflows/django.yml:22` and `.github/workflows/docker-build-push.yml:37` both set `node-version: 20`. `infra/Dockerfile:2` uses `FROM node:22-slim AS css-builder`.
- The mismatch is an oversight, not a decision. Commit `667e27f` says "infra: upgrade Node 20→22" but did not change the workflows. Nothing in docs/ or README pins Node 20, and there is no `.nvmrc` or `engines` field.
- The impact is small. Only the Tailwind CSS build runs on Node. CI still passes, and the shipped CSS is built on Node 22 inside the image. So the risk is drift, not a broken artifact. That makes it low, not medium.
- `docker-build-push.yml:39-42` ("Build CSS (preflight)") is redundant. The image build at `docker-build-push.yml:77` runs the Dockerfile `css-builder` stage, which builds the CSS again on Node 22. The CI output is never used.

## Critique of the proposal
Adding `.nvmrc` + `node-version-file` adds a third source of truth. The Dockerfile `FROM node:22-slim` cannot read `.nvmrc`, so the workflows and the image would still be able to drift.

## Better proposal (smallest diff)
1. `django.yml:22`: change `node-version: 20` to `node-version: 22`.
2. `docker-build-push.yml`: delete the "Set up Node.js" and "Build CSS (preflight)" steps (lines 34-42). The Dockerfile stage already builds the CSS on Node 22. If you want to keep the fail-fast check, change line 37 to `22` instead.
Effort: S.

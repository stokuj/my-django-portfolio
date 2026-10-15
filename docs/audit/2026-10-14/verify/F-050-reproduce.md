# F-050 - Transitive packages pinned as direct deps, some vulnerable

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning
- `pyproject.toml:7,14,18,20,21` pin `asgiref==3.8.1`, `packaging==25.0`, `pyjwt==2.12.0`, `sqlparse==0.5.4`, `tzdata==2025.2`.
- No `import`/`from` of asgiref, packaging, jwt, sqlparse or tzdata anywhere in the repo (rg over code, excluding lockfiles/node_modules).
- `.venv` reverse deps: asgiref, sqlparse <- django; packaging <- gunicorn, kombu; tzdata <- celery, kombu; pyjwt <- redis. So all five are transitive. Detail: pyjwt comes via `redis` (from `celery[redis]`), not django/gunicorn.
- `infra/Dockerfile:27` runs `uv pip install --system .`, which ignores uv.lock, so the pyproject pins are what production actually gets.
- OSV (queried 2026-10-15): sqlparse 0.5.4 has 5 advisories fixed in 0.6.0 (e.g. GHSA-prg7-hcfm-mfcr ReDoS, GHSA-3496-9g83-7v6x). pyjwt 2.12.0 has advisories fixed in 2.13.0/2.14.0/2.15.0 (e.g. GHSA-xgmm-8j9v-c9wx, GHSA-42vr-xj54-vc7v); latest is 2.15.1. tzdata latest is 2026.5 vs pinned 2025.2.
- Reachability: low. The app never calls PyJWT (redis only uses it for optional token auth), and Django uses sqlparse only for SQL formatting (migrations, debug), not on user input. That is why this stays medium hygiene and is not high.

## Better proposal
The proposal relies on F-045. `[tool.uv] constraint-dependencies` is applied by `uv lock`/`uv sync`. It is not applied by the current `uv pip install .`, so before F-045 it does nothing in the image.
- Now (S): bump the pins in place: `sqlparse>=0.6.0`, `pyjwt>=2.15.1`, `tzdata>=2026.5` (or exact equivalents), and re-lock.
- After F-045 (Dockerfile uses `uv sync --frozen`): drop the five transitive entries from `dependencies` and keep only CVE floors in `constraint-dependencies`.

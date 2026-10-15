# F-050 — Transitive packages pinned as direct deps, some vulnerable

**Verdict:** CONFIRMED (worth doing; proposal can be smaller and should not wait for F-045)
**Confidence:** high
**Adjusted severity:** medium (hygiene / Dependabot noise; no reachable exploit found)

## Reasoning
- `pyproject.toml:7,14,18,20,21` pin `asgiref==3.8.1`, `packaging==25.0`, `pyjwt==2.12.0`, `sqlparse==0.5.4`, `tzdata==2025.2`. None is imported in `django/`, `infra/`, `tests/` (grep for `jwt|sqlparse|packaging|asgiref|tzdata` imports: no hits).
- They are transitive (installed metadata): django 5.1.15 -> `asgiref>=3.8.1`, `sqlparse>=0.3.1`; redis 5.3.1 -> `PyJWT>=2.9.0`; kombu 5.6.2 -> `tzdata>=2025.2`, `packaging`; celery -> `tzdata>=2022.7`; gunicorn -> `packaging`.
- Advisories verified on PyPI JSON: sqlparse 0.5.4 has ~10 GHSA/PYSEC entries fixed in 0.6.0; pyjwt 2.12.0 has entries fixed in 2.12.1/2.13.0/2.14.0/2.15.0 (plus two with no fix listed). asgiref 3.8.1 and packaging 25.0 have none.
- Deliberate decision: `pyjwt==2.12.0` was added in `ec37bac` as a CVE floor for a transitive dep (Dependabot). Intent was "floor", but `==` turned it into a freeze; the finding's diagnosis holds.
- Reachability is low: app does not use redis token auth (PyJWT path) and Django uses sqlparse only for RunSQL splitting / SQL formatting, not user input. Hence medium, not high.

## Corrections to the proposal
- Risk statement is inverted: today `infra/Dockerfile:27` (`uv pip install --system .`) ignores `uv.lock`, so dropping these pins before F-045 makes Docker resolve the *newest* (patched) versions, not vulnerable ones. The only thing still holding 0.5.4 / 2.12.0 is the `==` pin itself (and `uv.lock` for CI).
- `[tool.uv] constraint-dependencies` is honored by project commands (`uv lock`/`sync`/`export`), not by the current `uv pip install .`, so it only helps after F-045. No need to block the security bump on F-045.

## Better proposal (smallest diff, works with and without F-045)
1. In `pyproject.toml` delete `asgiref`, `packaging`, `tzdata` (upstream floors already cover them).
2. Turn the two CVE floors into floors: `"pyjwt>=2.15.0"`, `"sqlparse>=0.6.0"` (or move them to `[tool.uv] constraint-dependencies` once F-045 lands, if keeping them out of `dependencies` matters).
3. `uv lock` and `make verify`.
Effort S. Risk: sqlparse 0.6.0 is a minor bump consumed only by Django internals; run `make verify` (migrations check covers RunSQL parsing).

# F-045 — Docker image ignores uv.lock; transitive deps float per build

**Verdict:** CONFIRMED (worth doing, proposal needs tightening)
**Confidence:** high
**Adjusted severity:** medium (reproducibility gap, not exploitable)

## Reasoning
- `infra/Dockerfile:21` copies `uv.lock`, but `infra/Dockerfile:27` runs `uv pip install --system --no-cache-dir .`, which resolves from `pyproject.toml` and never reads the lock.
- Direct deps are `==`-pinned (`pyproject.toml:6-22`), so only transitive deps float (e.g. urllib3, kombu, vine, billiard, redis, charset-normalizer, idna, certifi).
- CI tests the lock: `.github/workflows/django.yml:34` runs `uv sync --extra dev`; `Makefile:35-39` uses `uv run`. Prod therefore can run transitive versions CI never tested. Dependabot fixes landed in `uv.lock` (`ec37bac`) do not drive what ships.
- `infra/Dockerfile:26` `pip install uv` is unpinned.
- `uv lock --check` passes at HEAD ("Resolved 37 packages"), so switching to the lock is safe now.
- No deliberate decision to float found: `pip = { upgrade = true }` came in `a162562` ("Switch to uv...") with no rationale; `uv.lock` was added to the COPY in `109d310` (a .dockerignore/secret fix), suggesting lock use was intended.

## Corrections to the proposal
- `[tool.uv] pip.upgrade` (`pyproject.toml:29-30`) is not the cause in Docker: a fresh image has nothing installed, so `uv pip install .` picks newest anyway. Deleting it is optional cleanup; it only affects local `uv pip` use.
- Prefer `--locked` over `--frozen`: `--frozen` silently uses a stale lock; `--locked` fails the build if lock and pyproject drift.
- `uv sync` is the bigger diff here: it installs into `/app/.venv` (not system) and editable, so PATH/`UV_PROJECT_ENVIRONMENT` and the entrypoints would need changes. The export route keeps the system-site layout.

## Better proposal (smallest diff)
```dockerfile
COPY --from=ghcr.io/astral-sh/uv:<pinned-version> /uv /usr/local/bin/uv
RUN uv export --locked --no-emit-project -o /tmp/requirements.txt && \
    uv pip install --system --no-cache-dir -r /tmp/requirements.txt && \
    uv pip install --system --no-cache-dir --no-deps .
```
(or keep `pip install uv==<version>` if avoiding a new image source). Effort S. Risk: first build may downgrade some transitive versions vs the current image; run `make verify` + a dev compose smoke test.

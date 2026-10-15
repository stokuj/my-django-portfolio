# F-045 — Docker image ignores uv.lock; transitive deps float per build

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning

- `infra/Dockerfile:21` copies `uv.lock`, but `infra/Dockerfile:27` runs `uv pip install --system --no-cache-dir .`. The `uv pip` interface resolves from `pyproject.toml` and never reads `uv.lock`, so the lock is dead weight in the image.
- `pyproject.toml:6-22` pins only direct deps with `==`. Transitive deps (kombu, billiard, vine, redis, urllib3, certifi, idna, charset-normalizer, webencodings, etc.) are unconstrained and resolve to the newest compatible release at build time.
- CI (`.github/workflows/django.yml:34`) runs `uv sync --extra dev`, which installs from `uv.lock`. Prod (`.github/workflows/docker-build-push.yml`, `docker compose ... build web`) uses the Dockerfile path. So CI tests the locked set and prod ships a different set.
- Commit `ec37bac` bumped transitive `urllib3` 2.6.3 -> 2.7.0 and `pyjwt` (pinned directly, so that one does reach the image). The urllib3 bump exists only in `uv.lock`, which shows the lock is where the project tracks transitive versions, and the image ignores it.
- `infra/Dockerfile:26` `pip install --no-cache-dir uv` is unpinned: confirmed.

## Nuance (does not refute)

- `[tool.uv] pip = { upgrade = true }` (`pyproject.toml:29-30`) is not the cause. In a fresh `python:3.13-slim` layer nothing is installed, so an unlocked resolve already picks the newest versions. Without the lock, removing the table changes nothing. It is still worth deleting as dead config.
- Floating does not leave prod on vulnerable versions. It picks versions newer than the lock. The risk is reproducibility: an untested transitive release (for example a kombu or redis-py change) can reach prod without CI ever running it.

## Better proposal

The RUN shell is `/bin/sh`, so process substitution cannot be used. Minimal diff:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:<pinned-version> /uv /bin/uv
RUN uv export --frozen --no-dev --no-emit-project -o /tmp/req.txt && \
    uv pip install --system --no-cache-dir -r /tmp/req.txt && \
    uv pip install --system --no-cache-dir --no-deps .
```

Also delete the `[tool.uv] pip` table from `pyproject.toml:29-30`. Effort: S.

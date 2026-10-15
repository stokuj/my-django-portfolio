# F-102: Build toolchain (gcc, libpq-dev) shipped in runtime image

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low

## Reasoning
- `infra/Dockerfile:10` has only one Python stage (`python:3.13-slim`). The Node stage (`:2`) builds CSS only. So everything installed at `infra/Dockerfile:16-18` ends up in the runtime image: `gcc libpq-dev postgresql-client`.
- `pyproject.toml:16` pins `psycopg2-binary==2.9.10`, which ships with its own libpq. It needs neither `libpq-dev` (headers) nor `gcc`.
- The other direct deps (`pyproject.toml:7-21`) are pure Python, or Pillow 12.2.0, which has cp313 manylinux wheels. The project itself (`infra/Dockerfile:27`, setuptools, packages `main`/`config`) is pure Python. Nothing in the image build needs a compiler.
- `postgresql-client` is still in use: `django/entrypoints/wait-for-db.sh:15` calls `psql`, and both compose files use that script as the entrypoint (`infra/docker-compose.dev.yml:31`, `infra/docker-compose.prod.yml:42`). The finding is right to make removing it depend on F-048.
- Security impact: no attack path exists unless an attacker already has code execution in the container. A compiler then makes post-exploitation easier and adds CVE surface and image size. That is defense in depth, so low severity is correct.

## Caveat
`infra/Dockerfile:27` runs `uv pip install --system .`, which resolves from `pyproject.toml` and does not use `uv.lock`, with `[tool.uv] pip = { upgrade = true }`. A transitive dep could in theory resolve to a version without a wheel. The docker build would then fail loudly, not silently, so the stated risk holds.

## Better proposal
Change line 17 to `apt-get install -y --no-install-recommends postgresql-client`. Drop `postgresql-client` too once F-048 replaces `wait-for-db.sh` (e.g. with compose `depends_on: condition: service_healthy`). Effort S.

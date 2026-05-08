# Dev/Prod Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a split dev/prod Docker Compose workflow with a Makefile interface, automatic dev `.env` bootstrapping, strict prod `.env` enforcement, and a single `make verify` quality gate.

**Architecture:** Keep the current production stack intact by renaming the current compose file to `docker-compose.prod.yml`, introduce a separate `docker-compose.dev.yml` without Caddy, and move the fragile shell logic for status output and `.env` handling into two small Python helper scripts that the Makefile can call. Add focused unit tests for those helper scripts and file-level regression tests for the operational files so the workflow changes stay testable.

**Tech Stack:** GNU Make, Docker Compose v2, Python 3.13, `unittest`, Django management commands, Node/npm, Ruff.

---

## File Structure

- Create: `Makefile`
- Create: `docker-compose.dev.yml`
- Create: `scripts/__init__.py`
- Create: `scripts/ensure_env.py`
- Create: `scripts/compose_status.py`
- Create: `tests/__init__.py`
- Create: `tests/test_operational_helpers.py`
- Create: `tests/test_operational_files.py`
- Modify: `docker-compose.yml` (rename to `docker-compose.prod.yml`)
- Modify: `pyproject.toml`
- Modify: `.github/workflows/docker-build-push.yml`
- Modify: `.github/workflows/django.yml`
- Modify: `README.md`
- Modify: `docs/implementation.md`

The helper scripts are the main seam for testability:

- `scripts/ensure_env.py` owns `.env`/`.env.example` logic.
- `scripts/compose_status.py` owns formatted Docker status output.
- `Makefile` becomes a thin command router.
- `tests/test_operational_helpers.py` verifies helper behavior without talking to Docker.
- `tests/test_operational_files.py` verifies the generated operational files contain the intended commands and service boundaries.

---

### Task 1: Add helper-script tests first

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_operational_helpers.py`

- [ ] **Step 1: Write the failing helper tests**

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.compose_status import build_status_table
from scripts.ensure_env import ensure_env


class EnsureEnvTests(unittest.TestCase):
    def test_dev_mode_copies_example_when_env_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / ".env.example"
            env = root / ".env"
            example.write_text("SECRET_KEY=test\n", encoding="utf-8")

            created = ensure_env(env_path=env, example_path=example, create_if_missing=True)

            self.assertTrue(created)
            self.assertEqual(env.read_text(encoding="utf-8"), "SECRET_KEY=test\n")

    def test_prod_mode_fails_when_env_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / ".env.example"
            env = root / ".env"
            example.write_text("SECRET_KEY=test\n", encoding="utf-8")

            with self.assertRaises(FileNotFoundError):
                ensure_env(env_path=env, example_path=example, create_if_missing=False)

    def test_dev_mode_fails_when_example_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / ".env.example"
            env = root / ".env"

            with self.assertRaises(FileNotFoundError):
                ensure_env(env_path=env, example_path=example, create_if_missing=True)


class ComposeStatusTests(unittest.TestCase):
    def test_build_status_table_renders_header_and_rows(self):
        rows = [
            {
                "name": "portfolio-web-1",
                "status": "Up 10 seconds",
                "image": "my-django-portfolio:dev",
                "ports": "127.0.0.1:8000->8000/tcp",
            }
        ]

        table = build_status_table(rows)

        self.assertIn("NAME", table)
        self.assertIn("STATUS", table)
        self.assertIn("IMAGE", table)
        self.assertIn("PORTS", table)
        self.assertIn("portfolio-web-1", table)

    def test_build_status_table_handles_empty_rows(self):
        table = build_status_table([])
        self.assertIn("No matching containers found.", table)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the helper test file to verify it fails**

Run: `uv run python -m unittest tests.test_operational_helpers -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts'` or missing symbol errors from `scripts.ensure_env` / `scripts.compose_status`.

- [ ] **Step 3: Create the minimal helper implementations**

Create `scripts/__init__.py`:

```python
"""Operational helper scripts for local tooling."""
```

Create `scripts/ensure_env.py`:

```python
from pathlib import Path


def ensure_env(env_path: Path, example_path: Path, create_if_missing: bool) -> bool:
    if env_path.exists():
        return False

    if not example_path.exists():
        raise FileNotFoundError(f"Missing example env file: {example_path}")

    if not create_if_missing:
        raise FileNotFoundError(f"Missing env file: {env_path}")

    env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
    return True
```

Create `scripts/compose_status.py`:

```python
def build_status_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No matching containers found."

    headers = ["NAME", "STATUS", "IMAGE", "PORTS"]
    widths = {
        "NAME": max(len("NAME"), *(len(row["name"]) for row in rows)),
        "STATUS": max(len("STATUS"), *(len(row["status"]) for row in rows)),
        "IMAGE": max(len("IMAGE"), *(len(row["image"]) for row in rows)),
        "PORTS": max(len("PORTS"), *(len(row["ports"]) for row in rows)),
    }

    header = (
        f"{headers[0]:<{widths['NAME']}}  "
        f"{headers[1]:<{widths['STATUS']}}  "
        f"{headers[2]:<{widths['IMAGE']}}  "
        f"{headers[3]:<{widths['PORTS']}}"
    )

    lines = [header]
    for row in rows:
        lines.append(
            f"{row['name']:<{widths['NAME']}}  "
            f"{row['status']:<{widths['STATUS']}}  "
            f"{row['image']:<{widths['IMAGE']}}  "
            f"{row['ports']:<{widths['PORTS']}}"
        )

    return "\n".join(lines)
```

- [ ] **Step 4: Run the helper tests to verify they pass**

Run: `uv run python -m unittest tests.test_operational_helpers -v`
Expected: PASS with `Ran 5 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/__init__.py tests/test_operational_helpers.py scripts/__init__.py scripts/ensure_env.py scripts/compose_status.py
git commit -m "test: add coverage for workflow helper scripts"
```

---

### Task 2: Add file-level regression tests for Makefile and compose layout

**Files:**
- Create: `tests/test_operational_files.py`

- [ ] **Step 1: Write the failing file-level regression tests**

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


class OperationalFileTests(unittest.TestCase):
    def test_makefile_exists(self):
        self.assertTrue((ROOT / "Makefile").exists())

    def test_dev_compose_exists(self):
        self.assertTrue((ROOT / "docker-compose.dev.yml").exists())

    def test_prod_compose_exists(self):
        self.assertTrue((ROOT / "docker-compose.prod.yml").exists())

    def test_dev_compose_does_not_define_caddy(self):
        content = (ROOT / "docker-compose.dev.yml").read_text(encoding="utf-8")
        self.assertNotIn("\n  caddy:\n", content)

    def test_makefile_declares_required_targets(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        for target in [
            "dev-up:",
            "dev-status:",
            "dev-down:",
            "prod-up:",
            "prod-status:",
            "prod-down:",
            "verify:",
        ]:
            self.assertIn(target, content)

    def test_makefile_uses_helper_scripts(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("python scripts/ensure_env.py", content)
        self.assertIn("python scripts/compose_status.py", content)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the file-level regression tests to verify they fail**

Run: `uv run python -m unittest tests.test_operational_files -v`
Expected: FAIL because `Makefile`, `docker-compose.dev.yml`, and `docker-compose.prod.yml` do not exist yet.

- [ ] **Step 3: Leave the test file in place without implementation yet**

No new code in this step. The next task will make these tests pass.

- [ ] **Step 4: Commit the failing regression tests**

```bash
git add tests/test_operational_files.py
git commit -m "test: add regression coverage for workflow files"
```

---

### Task 3: Implement helper CLIs, compose split, and Makefile

**Files:**
- Modify: `scripts/ensure_env.py`
- Modify: `scripts/compose_status.py`
- Create: `Makefile`
- Create: `docker-compose.dev.yml`
- Modify: `docker-compose.yml` (rename to `docker-compose.prod.yml`)

- [ ] **Step 1: Extend `scripts/ensure_env.py` with CLI entrypoint**

Replace `scripts/ensure_env.py` with:

```python
from pathlib import Path
import argparse
import sys


def ensure_env(env_path: Path, example_path: Path, create_if_missing: bool) -> bool:
    if env_path.exists():
        return False

    if not example_path.exists():
        raise FileNotFoundError(f"Missing example env file: {example_path}")

    if not create_if_missing:
        raise FileNotFoundError(f"Missing env file: {env_path}")

    env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["dev", "prod"])
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--example-file", default=".env.example")
    args = parser.parse_args()

    try:
        created = ensure_env(
            env_path=Path(args.env_file),
            example_path=Path(args.example_file),
            create_if_missing=args.mode == "dev",
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if created:
        print(f"Created {args.env_file} from {args.example_file}.")
    else:
        print(f"Using existing {args.env_file}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Extend `scripts/compose_status.py` with Docker-aware CLI entrypoint**

Replace `scripts/compose_status.py` with:

```python
from __future__ import annotations

import argparse
import json
import subprocess
import sys


def build_status_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No matching containers found."

    headers = ["NAME", "STATUS", "IMAGE", "PORTS"]
    widths = {
        "NAME": max(len("NAME"), *(len(row["name"]) for row in rows)),
        "STATUS": max(len("STATUS"), *(len(row["status"]) for row in rows)),
        "IMAGE": max(len("IMAGE"), *(len(row["image"]) for row in rows)),
        "PORTS": max(len("PORTS"), *(len(row["ports"]) for row in rows)),
    }

    header = (
        f"{headers[0]:<{widths['NAME']}}  "
        f"{headers[1]:<{widths['STATUS']}}  "
        f"{headers[2]:<{widths['IMAGE']}}  "
        f"{headers[3]:<{widths['PORTS']}}"
    )

    lines = [header]
    for row in rows:
        lines.append(
            f"{row['name']:<{widths['NAME']}}  "
            f"{row['status']:<{widths['STATUS']}}  "
            f"{row['image']:<{widths['IMAGE']}}  "
            f"{row['ports']:<{widths['PORTS']}}"
        )

    return "\n".join(lines)


def load_rows(project_name: str) -> list[dict[str, str]]:
    command = [
        "docker",
        "ps",
        "-a",
        "--filter",
        f"label=com.docker.compose.project={project_name}",
        "--format",
        "{{json .}}",
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    rows: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        rows.append(
            {
                "name": parsed.get("Names", ""),
                "status": parsed.get("Status", ""),
                "image": parsed.get("Image", ""),
                "ports": parsed.get("Ports", ""),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_name")
    args = parser.parse_args()

    try:
        rows = load_rows(args.project_name)
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.strip() or "docker ps failed", file=sys.stderr)
        return 1

    print(build_status_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Rename the production compose file**

Run: `mv docker-compose.yml docker-compose.prod.yml`

Expected result: the current production stack moves intact to `docker-compose.prod.yml` with no content edits yet.

- [ ] **Step 4: Create `docker-compose.dev.yml`**

Create `docker-compose.dev.yml` with:

```yaml
services:
  db:
    image: postgres:13
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DOCKER_DB_NAME}
      POSTGRES_USER: ${DOCKER_DB_USER}
      POSTGRES_PASSWORD: ${DOCKER_DB_PASSWORD}
    ports:
      - "127.0.0.1:15432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - app-network

  web:
    build: .
    image: my-django-portfolio:dev
    user: "10001:10001"
    env_file:
      - .env
    working_dir: /app/django
    entrypoint: ["sh", "/app/django/entrypoints/wait-for-db.sh"]
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - media_dev_volume:/app/media
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DJANGO_DEBUG=${DJANGO_DEBUG}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}
      - DB_ENGINE=${DOCKER_DB_ENGINE}
      - DB_NAME=${DOCKER_DB_NAME}
      - DB_USER=${DOCKER_DB_USER}
      - DB_PASSWORD=${DOCKER_DB_PASSWORD}
      - DB_HOST=${DOCKER_DB_HOST}
      - DB_PORT=${DOCKER_DB_PORT}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - db
      - redis
    networks:
      - app-network

  worker:
    build: .
    image: my-django-portfolio:dev
    user: "10001:10001"
    restart: unless-stopped
    env_file:
      - .env
    working_dir: /app/django
    command: >
      sh -c "sleep ${WORKER_START_DELAY_SECONDS:-45} &&
             celery -A config worker --loglevel=info"
    volumes:
      - media_dev_volume:/app/media
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DJANGO_DEBUG=${DJANGO_DEBUG}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}
      - DB_ENGINE=${DOCKER_DB_ENGINE}
      - DB_NAME=${DOCKER_DB_NAME}
      - DB_USER=${DOCKER_DB_USER}
      - DB_PASSWORD=${DOCKER_DB_PASSWORD}
      - DB_HOST=${DOCKER_DB_HOST}
      - DB_PORT=${DOCKER_DB_PORT}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - db
      - redis
      - web
    networks:
      - app-network

  beat:
    build: .
    image: my-django-portfolio:dev
    user: "10001:10001"
    restart: unless-stopped
    env_file:
      - .env
    working_dir: /app/django
    command: celery -A config beat --loglevel=info --schedule=/app/django/celerybeat-schedule/celerybeat-schedule.db
    volumes:
      - celerybeat_dev_schedule:/app/django/celerybeat-schedule
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DJANGO_DEBUG=${DJANGO_DEBUG}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}
      - DB_ENGINE=${DOCKER_DB_ENGINE}
      - DB_NAME=${DOCKER_DB_NAME}
      - DB_USER=${DOCKER_DB_USER}
      - DB_PASSWORD=${DOCKER_DB_PASSWORD}
      - DB_HOST=${DOCKER_DB_HOST}
      - DB_PORT=${DOCKER_DB_PORT}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - db
      - redis
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_dev_data:
  media_dev_volume:
  celerybeat_dev_schedule:
```

- [ ] **Step 5: Create `Makefile`**

Create `Makefile` with:

```make
.PHONY: dev-up dev-down dev-status prod-up prod-down prod-status verify

DEV_COMPOSE := docker compose -p my-django-portfolio-dev -f docker-compose.dev.yml
PROD_COMPOSE := docker compose -p my-django-portfolio-prod -f docker-compose.prod.yml
PYTHON := uv run python

dev-up:
	$(PYTHON) scripts/ensure_env.py dev
	$(DEV_COMPOSE) up --build -d

dev-down:
	$(DEV_COMPOSE) down

dev-status:
	$(PYTHON) scripts/compose_status.py my-django-portfolio-dev

prod-up:
	$(PYTHON) scripts/ensure_env.py prod
	$(PROD_COMPOSE) up --build -d

prod-down:
	$(PROD_COMPOSE) down

prod-status:
	$(PYTHON) scripts/compose_status.py my-django-portfolio-prod

verify:
	npm run build:css:prod
	$(PYTHON) -m compileall django
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 $(PYTHON) django/manage.py check
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 $(PYTHON) django/manage.py makemigrations --check --dry-run
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 $(PYTHON) django/manage.py test
	uv run ruff check .
```

- [ ] **Step 6: Run the file-level regression tests to verify they pass**

Run: `uv run python -m unittest tests.test_operational_files -v`
Expected: PASS with `Ran 6 tests` and `OK`.

- [ ] **Step 7: Commit**

```bash
git add Makefile docker-compose.dev.yml docker-compose.prod.yml scripts/ensure_env.py scripts/compose_status.py tests/test_operational_files.py
git commit -m "feat: add dev and prod compose workflow"
```

---

### Task 4: Add Ruff and align CI with the new workflow

**Files:**
- Modify: `pyproject.toml`
- Modify: `.github/workflows/docker-build-push.yml`
- Modify: `.github/workflows/django.yml`

- [ ] **Step 1: Write the failing check for Ruff availability**

Run: `uv run ruff --version`
Expected: FAIL with a message indicating `ruff` is not installed.

- [ ] **Step 2: Add Ruff configuration and dependency declaration**

Replace `pyproject.toml` with:

```toml
[project]
name = "my-django-portfolio"
version = "0.2.5"
description = "My portfolio website, created using Django/TailwindCSS"
requires-python = ">=3.13,<3.14"
dependencies = [
    "asgiref==3.8.1",
    "bleach==6.2.0",
    "celery[redis]==5.4.0",
    "django==5.1.15",
    "django-environ==0.12.0",
    "gunicorn==23.0.0",
    "markdown==3.8.2",
    "packaging==25.0",
    "pillow==12.1.1",
    "psycopg2-binary==2.9.10",
    "pymdown-extensions==10.16.1",
    "requests==2.32.5",
    "ruff==0.11.10",
    "sqlparse==0.5.4",
    "tzdata==2025.2",
]

[tool.uv]
pip = { upgrade = true }

[tool.setuptools]
packages = ["main", "config"]

[tool.setuptools.package-dir]
"" = "django"

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

- [ ] **Step 3: Update the Docker image workflow to reference the production compose file**

Edit `.github/workflows/docker-build-push.yml` so the build and deploy commands become:

```yaml
      - name: Build images with Docker Compose
        run: docker compose -f docker-compose.prod.yml build web

      - name: Push images to GitHub Container Registry
        run: docker compose -f docker-compose.prod.yml push web
```

and in the deploy script:

```yaml
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d --remove-orphans --force-recreate
```

- [ ] **Step 4: Update the Django CI workflow to use `make verify`**

Replace the install-and-test section in `.github/workflows/django.yml` with:

```yaml
    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv sync

    - name: Create .env file
      run: |
        echo "SECRET_KEY=django-insecure-test-key-for-ci" > .env
        echo "DJANGO_DEBUG=True" >> .env
        echo "ALLOWED_HOSTS=localhost,127.0.0.1" >> .env

    - name: Run Verification
      run: make verify
```

- [ ] **Step 5: Re-sync dependencies and verify Ruff is now installed**

Run: `uv sync && uv run ruff --version`
Expected: PASS with a printed Ruff version such as `ruff 0.11.10`.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .github/workflows/docker-build-push.yml .github/workflows/django.yml
git commit -m "ci: align verification with make workflow"
```

---

### Task 5: Update developer documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/implementation.md`

- [ ] **Step 1: Write the failing doc regression check**

Run: `grep -n "docker-compose.yml\|docker compose up --build -d\|make dev-up\|make verify" README.md docs/implementation.md`
Expected: output still references the old root compose filename and does not yet document the new Makefile workflow completely.

- [ ] **Step 2: Update `README.md` operational sections**

Make these content changes:

```md
## Quick Start (Docker)

### Development

```bash
make dev-up
make dev-status
make dev-down
```

Open `http://localhost:8000`.

`make dev-up` creates `.env` from `.env.example` when needed.

### Production

```bash
make prod-up
make prod-status
make prod-down
```

`make prod-up` requires an existing `.env` file and fails if it is missing.

## Verification Commands

```bash
make verify
```
```

Also update the project structure and troubleshooting references from `docker-compose.yml` to `docker-compose.prod.yml`, and mention that local development does not use Caddy.

- [ ] **Step 3: Update `docs/implementation.md` runtime and workflow sections**

Make these content changes:

```md
- Root operational files: `docker-compose.dev.yml`, `docker-compose.prod.yml`, `Dockerfile`, `Caddyfile`, `Makefile`, `pyproject.toml`, `package.json`.
```

```md
Services are defined in `docker-compose.prod.yml`:
```

Add a short new subsection under runtime:

```md
### Development Compose Services

Local development uses `docker-compose.dev.yml` with `db`, `redis`, `web`, `worker`, and `beat`. It does not include Caddy; Django is exposed directly on port `8000`.
```

Replace the setup and core checks section with:

```md
### Setup

```bash
uv sync
npm install
make dev-up
```

### Core Checks

```bash
make verify
```
```

- [ ] **Step 4: Re-run the doc regression check to verify updated references**

Run: `grep -n "docker-compose.yml\|docker-compose.prod.yml\|make dev-up\|make verify" README.md docs/implementation.md`
Expected: PASS with `docker-compose.prod.yml`, `make dev-up`, and `make verify` present, and no stale operational instruction that tells users to run the old root compose file directly.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/implementation.md
git commit -m "docs: document dev and prod make workflow"
```

---

### Task 6: Full verification and branch cleanup

**Files:**
- Verify only: all files changed in Tasks 1-5

- [ ] **Step 1: Validate both compose files parse correctly**

Run: `docker compose -f docker-compose.dev.yml config >/tmp/dev-compose-config.txt && docker compose -f docker-compose.prod.yml config >/tmp/prod-compose-config.txt`
Expected: PASS with exit code `0` for both commands.

- [ ] **Step 2: Run the helper and file regression tests together**

Run: `uv run python -m unittest tests.test_operational_helpers tests.test_operational_files -v`
Expected: PASS with all helper and file-level tests green.

- [ ] **Step 3: Run the complete project verification command**

Run: `make verify`
Expected: PASS with successful CSS build, `compileall`, `manage.py check`, `makemigrations --check --dry-run`, full Django test run, and `ruff check .`.

- [ ] **Step 4: Exercise the operational commands manually**

Run: `rm -f .env && make dev-up && make dev-status && make dev-down`
Expected: PASS. `make dev-up` recreates `.env`, starts containers, `make dev-status` prints a readable table, and `make dev-down` stops the dev stack.

- [ ] **Step 5: Verify production refuses to start without `.env`**

Run: `rm -f .env && make prod-up`
Expected: FAIL fast with a clear missing `.env` message and no containers started.

- [ ] **Step 6: Restore `.env` from example for local safety**

Run: `cp .env.example .env`
Expected: PASS with `.env` present again in the working tree.

- [ ] **Step 7: Commit the final implementation checkpoint**

```bash
git add Makefile docker-compose.dev.yml docker-compose.prod.yml scripts tests pyproject.toml uv.lock .github/workflows README.md docs/implementation.md
git commit -m "feat: add dev and prod docker workflow"
```

---

## Spec Coverage Check

- `make dev-up`, `make dev-status`, `make dev-down`: Tasks 2, 3, and 6.
- `make prod-up`, `make prod-status`, `make prod-down`: Tasks 2, 3, and 6.
- automatic `.env` copy in dev: Tasks 1, 3, and 6.
- prod startup failure without `.env`: Tasks 1, 3, and 6.
- separate dev compose without Caddy: Tasks 2, 3, and 6.
- production compose renamed to `docker-compose.prod.yml`: Tasks 2, 3, 4, and 5.
- `make verify` with tests and linters: Tasks 3, 4, and 6.
- documentation and CI alignment: Tasks 4 and 5.

## Self-Review Notes

- Placeholder scan: no unfinished markers or deferred implementation notes remain.
- Scope check: the plan stays within one subsystem, the operational workflow around Docker/Make/verification.
- Naming consistency: all plan steps use `docker-compose.dev.yml`, `docker-compose.prod.yml`, `scripts/ensure_env.py`, `scripts/compose_status.py`, and `make verify` consistently.

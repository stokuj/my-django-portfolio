# Issue 55 Prod Workflow Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the production workflow so it reuses the original `my_django_portfolio` Docker volumes, runs without Python/uv on the droplet, and the CI deploy script is aligned with the same project name.

**Architecture:** Minimal 3-file change. Revert the production Compose project name from `my-django-portfolio-prod` back to `my_django_portfolio`. Replace Python-dependent `prod-up` and `prod-status` targets with pure shell + Docker commands. Keep dev and verify targets unchanged. Add regression tests before implementation.

**Tech Stack:** GNU Make, Docker Compose v2, shell `test`, `docker ps --format`, Python `unittest`.

---

## File Structure

- Modify: `tests/test_operational_files.py` — regression assertions on new prod target shape
- Modify: `Makefile` — revert project name, shell-only prod targets
- Modify: `.github/workflows/docker-build-push.yml` — align deploy with project name

Only 3 files touched. No new files created. No files deleted.

---

### Task 1: Write failing regression tests

**Files:**
- Modify: `tests/test_operational_files.py`

- [ ] **Step 1: Write the failing regression tests**

Replace `tests/test_operational_files.py` with:

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class OperationalFileTests(unittest.TestCase):
    def test_makefile_exists(self):
        self.assertTrue((ROOT / "Makefile").exists())

    def test_dev_compose_exists(self):
        self.assertTrue((ROOT / "infra/docker-compose.dev.yml").exists())

    def test_prod_compose_exists(self):
        self.assertTrue((ROOT / "infra/docker-compose.prod.yml").exists())

    def test_dev_compose_does_not_define_caddy(self):
        content = (ROOT / "infra/docker-compose.dev.yml").read_text(encoding="utf-8")
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
        self.assertIn("python infra/scripts/ensure_env.py", content)
        self.assertIn("python infra/scripts/compose_status.py", content)

    def test_makefile_passes_root_env_file_to_compose(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("docker compose --env-file .env -p my-django-portfolio-dev", content)
        self.assertIn("docker compose --env-file .env -p my_django_portfolio", content)

    def test_dev_compose_uses_root_context_and_infra_dockerfile(self):
        content = (ROOT / "infra/docker-compose.dev.yml").read_text(encoding="utf-8")
        self.assertIn("context: ..", content)
        self.assertIn("dockerfile: infra/Dockerfile", content)

    def test_prod_compose_uses_root_context_and_infra_dockerfile(self):
        content = (ROOT / "infra/docker-compose.prod.yml").read_text(encoding="utf-8")
        self.assertEqual(content.count("context: .."), 3)
        self.assertEqual(content.count("dockerfile: infra/Dockerfile"), 3)

    def test_prod_compose_uses_root_env_file_for_all_app_services(self):
        content = (ROOT / "infra/docker-compose.prod.yml").read_text(encoding="utf-8")
        self.assertEqual(content.count("- ../.env"), 3)

    def test_prod_up_uses_shell_env_guard(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("test -f .env", content)

    def test_prod_status_uses_docker_ps_not_python(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("docker ps", content)

    def test_makefile_uses_original_prod_project_name(self):
        content = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("-p my_django_portfolio", content)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the file-level regression tests to verify they fail**

Run: `uv run python -m unittest tests.test_operational_files -v`

Expected: 3 tests FAIL:
- `test_makefile_passes_root_env_file_to_compose` — still has `my-django-portfolio-prod`
- `test_prod_up_uses_shell_env_guard` — still uses `python`
- `test_prod_status_uses_docker_ps_not_python` — still uses `python`

- [ ] **Step 3: Commit the failing regression tests**

```bash
git add tests/test_operational_files.py
git commit -m "test: add regression coverage for issue 55 prod workflow fix"
```

---

### Task 2: Implement Makefile and CI changes to pass the tests

**Files:**
- Modify: `Makefile`
- Modify: `.github/workflows/docker-build-push.yml`

- [ ] **Step 1: Update `Makefile` with original project name and shell-only prod targets**

Replace `Makefile` with:

```makefile
.PHONY: dev-up dev-down dev-status prod-up prod-down prod-status verify

DEV_COMPOSE := docker compose --env-file .env -p my-django-portfolio-dev -f infra/docker-compose.dev.yml
PROD_COMPOSE := docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml

dev-up:
	uv run python infra/scripts/ensure_env.py dev
	$(DEV_COMPOSE) up --build -d

dev-down:
	$(DEV_COMPOSE) down

dev-status:
	uv run python infra/scripts/compose_status.py my-django-portfolio-dev

prod-up:
	@test -f .env || { echo "Error: .env file is missing. Create it first."; exit 1; }
	$(PROD_COMPOSE) up -d

prod-down:
	$(PROD_COMPOSE) down

prod-status:
	@docker ps -a \
		--filter "label=com.docker.compose.project=my_django_portfolio" \
		--format "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"

verify:
	npm run build:css:prod
	uv run python -m compileall django
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py check
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py makemigrations --check --dry-run
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py test
	uv run ruff check infra/scripts tests
```

- [ ] **Step 2: Update CI deploy script with `-p my_django_portfolio`**

Replace the two `docker compose` lines in `.github/workflows/docker-build-push.yml` (around lines 107-108):

From:
```yaml
            docker compose --env-file .env -f infra/docker-compose.prod.yml pull
            docker compose --env-file .env -f infra/docker-compose.prod.yml up -d --remove-orphans --force-recreate
```

To:
```yaml
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml pull
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml up -d --remove-orphans --force-recreate
```

- [ ] **Step 3: Run the regression tests to verify they pass**

Run: `uv run python -m unittest tests.test_operational_files -v`

Expected: all 13 file-level tests PASS.

- [ ] **Step 4: Commit**

```bash
git add Makefile .github/workflows/docker-build-push.yml
git commit -m "fix: restore original prod project name and remove python dependency from prod targets"
```

---

### Task 3: Full verification

**Files:**
- Verify only: all files changed in Tasks 1-2

- [ ] **Step 1: Validate both compose files parse correctly**

Run:
```bash
docker compose -f infra/docker-compose.dev.yml config >/dev/null && echo "dev: OK" || echo "dev: FAIL"
docker compose -f infra/docker-compose.prod.yml config >/dev/null && echo "prod: OK" || echo "prod: FAIL"
```
Expected: both OK.

- [ ] **Step 2: Run all test suites**

Run: `uv run python -m unittest tests.test_operational_helpers tests.test_operational_files -v`
Expected: all 17 tests PASS.

- [ ] **Step 3: Run full `make verify`**

Run: `make verify`
Expected: PASS.

- [ ] **Step 4: Commit and push**

```bash
git status --short
# If clean, done. If any leftover changes, commit them.
git push origin feature/55-fix-prod-workflow-data-loss
```

---

## Spec Coverage Check

| Requirement | Task |
|-------------|------|
| Restore `my_django_portfolio` project name in Makefile | Task 2 |
| `prod-up` without Python/uv | Task 2 |
| `prod-status` without Python/uv | Task 2 |
| CI deploy uses `-p my_django_portfolio` | Task 2 |
| Dev targets unchanged | Tasks 1-2 (tests confirm) |
| Regression tests on project name and shell targets | Task 1 |
| Full verification (`make verify`, all tests) | Task 3 |

## Self-Review Notes

- Placeholder scan: no unfinished markers or deferred implementation notes remain.
- Scope check: 3 files, 3 tasks, focused on Issue #55 only.
- Naming consistency: `my_django_portfolio` (with underscores, original name) used consistently throughout.
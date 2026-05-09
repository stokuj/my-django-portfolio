# Issue 57 Disk Space Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add log rotation to all production services and improve deploy script cleanup to prevent disk space exhaustion on the 10 GB droplet.

**Architecture:** Two config-only files changed. Add `logging:` blocks to six services in `infra/docker-compose.prod.yml`, and extend the deploy script in `.github/workflows/docker-build-push.yml` with orphan cleanup and aggressive image/builder pruning. Verify with string-assertion regression tests in `tests/test_operational_files.py`.

**Tech Stack:** Docker Compose v2, GitHub Actions, Python `unittest`.

---

## File Structure

- Modify: `tests/test_operational_files.py` — new regression assertions
- Modify: `infra/docker-compose.prod.yml` — log rotation on all services
- Modify: `.github/workflows/docker-build-push.yml` — deploy cleanup improvements

Only 3 files. No new files created, no files deleted.

---

### Task 1: Write failing regression tests

**Files:**
- Modify: `tests/test_operational_files.py`

- [ ] **Step 1: Add failing assertions for logging and deploy cleanup**

Append these 6 new test methods to the `OperationalFileTests` class in `tests/test_operational_files.py`, after the existing `test_makefile_uses_original_prod_project_name` method (line 68):

```python
    def test_prod_compose_all_services_have_logging(self):
        content = (ROOT / "infra/docker-compose.prod.yml").read_text(encoding="utf-8")
        self.assertEqual(content.count("    logging:"), 6)

    def test_prod_compose_logging_has_rotation(self):
        content = (ROOT / "infra/docker-compose.prod.yml").read_text(encoding="utf-8")
        self.assertIn('max-size: "10m"', content)
        self.assertIn('max-file: "3"', content)

    def test_deploy_script_has_down_before_up(self):
        content = (ROOT / ".github/workflows/docker-build-push.yml").read_text(encoding="utf-8")
        self.assertIn("down --remove-orphans", content)

    def test_deploy_script_has_builder_prune(self):
        content = (ROOT / ".github/workflows/docker-build-push.yml").read_text(encoding="utf-8")
        self.assertIn("docker builder prune -af", content)

    def test_deploy_script_has_image_prune_all(self):
        content = (ROOT / ".github/workflows/docker-build-push.yml").read_text(encoding="utf-8")
        self.assertIn("docker image prune -af", content)

    def test_deploy_script_prune_runs_after_up(self):
        content = (ROOT / ".github/workflows/docker-build-push.yml").read_text(encoding="utf-8")
        up_index = content.index("up -d --force-recreate")
        prune_index = content.index("docker image prune -af")
        self.assertGreater(prune_index, up_index)
```

- [ ] **Step 2: Run the regression tests to verify they fail**

Run: `uv run python -m unittest tests.test_operational_files -v`

Expected: 6 new tests FAIL, total 19 tests (13 pass + 6 fail), because:
- prod compose has 0 `logging:` blocks (need 6)
- deploy script has no `down --remove-orphans`
- deploy script has no `docker builder prune -af`
- deploy script has `docker image prune -f` (not `-af`)
- deploy script doesn't have prune after up (only has `docker image prune -f`)

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_operational_files.py
git commit -m "test: add regression coverage for issue 57 disk optimization"
```

---

### Task 2: Implement compose logging and deploy cleanup

**Files:**
- Modify: `infra/docker-compose.prod.yml`
- Modify: `.github/workflows/docker-build-push.yml`

- [ ] **Step 1: Add logging rotation to all prod services**

Add the following block after the `networks:` line of each of the 6 services in `infra/docker-compose.prod.yml`:

```yaml
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

The services are: `db` (ends at line 15), `redis` (ends at line 21), `web` (ends at line 59), `worker` (ends at line 94), `beat` (ends at line 126), `caddy` (ends at line 149).

For example, `db` currently ends with:

```yaml
    networks:
      - app-network
```
Add `logging:` block after `networks:` for each service.

- [ ] **Step 2: Update the deploy script**

Replace the final lines of the deploy script in `.github/workflows/docker-build-push.yml`:

From:
```yaml
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml pull
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml up -d --remove-orphans --force-recreate

            docker image prune -f
```

To (keeping exact 12-space indentation):
```yaml
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml pull
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml down --remove-orphans
            docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml up -d --force-recreate

            docker builder prune -af
            docker image prune -af
```

Note: `--remove-orphans` moves from `up` to `down`. `image prune -f` becomes `image prune -af`.

- [ ] **Step 3: Run all regression tests to verify they pass**

Run: `uv run python -m unittest tests.test_operational_files -v`

Expected: all 19 file-level tests PASS.

Run: `uv run python -m unittest tests.test_operational_helpers tests.test_operational_files -v`

Expected: all 26 tests PASS (7 helper + 19 file-level).

- [ ] **Step 4: Commit**

```bash
git add infra/docker-compose.prod.yml .github/workflows/docker-build-push.yml
git commit -m "feat: add log rotation and disk cleanup to prod workflow"
```

---

### Task 3: Final verification

**Files:**
- Verify only: all files changed in Tasks 1-2

- [ ] **Step 1: Validate both compose files parse**

```bash
docker compose -f infra/docker-compose.dev.yml config >/dev/null && echo "dev: OK" || echo "dev: FAIL"
docker compose -f infra/docker-compose.prod.yml config >/dev/null && echo "prod: OK" || echo "prod: FAIL"
```
Expected: both OK.

- [ ] **Step 2: Run full test suite**

```bash
uv run python -m unittest tests.test_operational_helpers tests.test_operational_files -v
```
Expected: 26 tests, all PASS.

- [ ] **Step 3: Run `make verify`**

```bash
make verify
```
Expected: PASS.

- [ ] **Step 4: Check working tree is clean**

```bash
git status --short
```
Expected: no untracked/modified files.

- [ ] **Step 5: Push**

```bash
git push origin feature/57-disk-space-optimization
```

---

## Spec Coverage Check

| Requirement | Task |
|-------------|------|
| Log rotation on all 6 prod services | Task 2 |
| `max-size: 10m`, `max-file: 3` | Tasks 1-2 (tests + impl) |
| `down --remove-orphans` before `up` in deploy | Tasks 1-2 |
| `docker builder prune -af` in deploy | Tasks 1-2 |
| `docker image prune -af` in deploy (all, not dangling) | Tasks 1-2 |
| Verify passes | Task 3 |

## Self-Review Notes

- Placeholder scan: no unfinished markers or deferred implementation notes remain.
- Scope check: 3 files, 2 config changes, 1 test file. Focused on Issue #57 only.
- Naming consistency: `logging:`, `down --remove-orphans`, `builder prune -af`, `image prune -af` used consistently throughout.
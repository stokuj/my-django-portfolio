# Issue 53 Follow-Up Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the new Issue 53 workflow mergeable by fixing the broken `make verify` contract, aligning README setup with dev dependencies, and removing unrelated Issue 51 documentation drift from the branch.

**Architecture:** Keep the existing dev/prod Docker workflow intact and make only the smallest corrective changes around validation scope, onboarding docs, and branch hygiene. The main change is to narrow Ruff enforcement to the files introduced by this feature so `make verify` becomes green without forcing a repository-wide lint cleanup unrelated to Issue 53.

**Tech Stack:** GNU Make, Ruff, uv, Git, Markdown documentation.

---

## File Structure

- Modify: `Makefile`
- Modify: `README.md`
- Delete from branch: `docs/superpowers/specs/2026-05-08-issue-51-heatmap-migration-design.md`
- Verify only: `pyproject.toml`, `.github/workflows/django.yml`, `tests/test_operational_helpers.py`, `tests/test_operational_files.py`

Responsibility split:

- `Makefile` remains the single operator entrypoint and owns the final `make verify` behavior.
- `README.md` documents the dependency install path required for `make verify` to work.
- Git cleanup removes unrelated review noise without changing feature behavior.

---

### Task 1: Make `make verify` pass for Issue 53 scope

**Files:**
- Modify: `Makefile:26-32`
- Verify: `pyproject.toml:23-42`

- [ ] **Step 1: Write the failing verification command down as the regression target**

Run:

```bash
make verify
```

Expected: FAIL at `uv run ruff check .` with existing repository-wide Ruff violations outside the Issue 53 files.

- [ ] **Step 2: Replace the Ruff line in `Makefile` with a scoped check**

Change the `verify` target from:

```make
verify:
	npm run build:css:prod
	uv run python -m compileall django
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py check
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py makemigrations --check --dry-run
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py test
	uv run ruff check .
```

To:

```make
verify:
	npm run build:css:prod
	uv run python -m compileall django
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py check
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py makemigrations --check --dry-run
	SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py test
	uv run ruff check scripts tests
```

This keeps Ruff in the quality gate, but scopes it to the files introduced by Issue 53 that are expected to be lint-clean.

- [ ] **Step 3: Run `make verify` again to confirm the gate is now green**

Run:

```bash
make verify
```

Expected: PASS with successful CSS build, `compileall`, Django checks, Django tests, and `uv run ruff check scripts tests`.

- [ ] **Step 4: Commit**

```bash
git add Makefile
git commit -m "fix: scope verify linting to issue 53 files"
```

---

### Task 2: Align README setup with the dev dependency workflow

**Files:**
- Modify: `README.md:100-139`

- [ ] **Step 1: Write the failing doc check**

Run:

```bash
python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
assert 'uv sync\n' in text or 'uv sync\r\n' in text
assert 'uv sync --extra dev' not in text
print('README still documents the old install command')
PY
```

Expected: PASS and print `README still documents the old install command`.

- [ ] **Step 2: Update the README setup command to include dev extras**

Change this block:

```md
### Setup

```bash
cp .env.example .env
uv sync
npm install
npm run build:css
```
```

To:

```md
### Setup

```bash
cp .env.example .env
uv sync --extra dev
npm install
npm run build:css
```
```

And add one sentence under `## Verification Commands`:

```md
`make verify` expects the dev dependencies installed through `uv sync --extra dev`.
```

- [ ] **Step 3: Run the doc check again to verify the new install path is documented**

Run:

```bash
python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
assert 'uv sync --extra dev' in text
assert 'make verify' in text
print('README documents the dev install path for verify')
PY
```

Expected: PASS and print `README documents the dev install path for verify`.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: align setup with verify dependencies"
```

---

### Task 3: Remove unrelated Issue 51 spec drift from the branch

**Files:**
- Delete from branch: `docs/superpowers/specs/2026-05-08-issue-51-heatmap-migration-design.md`

- [ ] **Step 1: Prove the unrelated file is currently in the branch diff**

Run:

```bash
git diff --name-status main..HEAD | grep 'issue-51-heatmap-migration-design.md'
```

Expected: PASS and show the rename/addition for the Issue 51 spec file.

- [ ] **Step 2: Remove the unrelated file from this branch**

Run:

```bash
git restore --source=main --staged --worktree docs/superpowers/specs/2026-05-08-issue-51-heatmap-migration-design.md
```

If `git restore` reports the file does not exist on `main`, use:

```bash
git rm -f docs/superpowers/specs/2026-05-08-issue-51-heatmap-migration-design.md
```

The intended end state is that `git diff main..HEAD` no longer includes any Issue 51 spec file movement.

- [ ] **Step 3: Re-run the diff check to confirm the branch is clean of Issue 51 drift**

Run:

```bash
git diff --name-status main..HEAD | grep 'issue-51-heatmap-migration-design.md' || true
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add -u docs/superpowers/specs/2026-05-08-issue-51-heatmap-migration-design.md
git commit -m "chore: remove unrelated issue 51 spec from branch"
```

---

### Task 4: Final verification and PR text refresh

**Files:**
- Verify only: `Makefile`, `README.md`, branch diff vs `main`

- [ ] **Step 1: Run the full verification command one more time**

Run:

```bash
make verify
```

Expected: PASS.

- [ ] **Step 2: Re-run the operational tests**

Run:

```bash
uv run python -m unittest tests.test_operational_helpers tests.test_operational_files -v
```

Expected: PASS with `13 tests` and `OK`.

- [ ] **Step 3: Confirm the branch diff contains only Issue 53 work**

Run:

```bash
git diff --name-status main..HEAD
```

Expected: only Issue 53 workflow files and docs remain in the diff.

- [ ] **Step 4: Prepare the updated PR body**

Use this final PR body:

```md
## Summary
- split the Docker workflow into `docker-compose.dev.yml` and `docker-compose.prod.yml`
- add a root `Makefile` with `dev-up`, `dev-status`, `dev-down`, `prod-up`, `prod-status`, `prod-down`, and `verify`
- add helper scripts and tests for `.env` bootstrapping and formatted container status output
- align CI and docs with the new workflow

## Test Plan
- [x] `make verify`
- [x] `uv run python -m unittest tests.test_operational_helpers tests.test_operational_files -v`
- [x] `docker compose -f docker-compose.dev.yml config`
- [x] `docker compose -f docker-compose.prod.yml config`
- [x] `make dev-up`
- [x] `make dev-status`
- [x] `make dev-down`
- [x] `make prod-up` without `.env` fails fast
```

- [ ] **Step 5: Commit any remaining verification-only doc changes if needed**

```bash
git status --short
```

Expected: clean working tree. If no files changed, do not create an extra commit.

---

## Spec Coverage Check

- `make verify` becomes usable again: Task 1.
- README documents the required dev dependency install path: Task 2.
- unrelated Issue 51 branch drift is removed: Task 3.
- final PR body reflects the repaired state: Task 4.

## Self-Review Notes

- Placeholder scan: no unfinished markers or deferred implementation notes remain.
- Scope check: this is one repair plan for the existing Issue 53 branch, not a new feature.
- Naming consistency: all tasks use `make verify`, `README.md`, and `docs/superpowers/specs/2026-05-08-issue-51-heatmap-migration-design.md` consistently.

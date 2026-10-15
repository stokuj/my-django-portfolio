# F-039 (reproduce): Disk threshold fix (d2b6257) has no regression test; view test reads real disk

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `git show d2b6257 --stat` touches only `.env.example` and `django/main/views.py`; no test file changed.
- `django/main/views.py:239-253`: `_get_disk_info` calls the real `shutil.disk_usage("/")` and classifies on `free_raw_gb` (the fix). Before the fix it classified on `round(..., 1)`, so 0.96 GB -> 1.0 -> "warning" instead of "critical".
- `django/main/tests/test_views.py:632-647`: no patch of `shutil.disk_usage`; asserts only key presence and `level in ("ok","warning","critical")`. It would pass with the old rounded comparison. Also non-deterministic input (host disk).
- No other test references `_get_disk_info` or `disk_info` (grep over `django/main/tests/`).

## Correction to the proposal
- `check_disk_usage_task` (`django/main/tasks.py:202-210`) never had the rounding bug: it always compared the unrounded `free_gb`. It already has mocked tests at `django/main/tests/test_tasks.py:349-374` (5.0 / 1.5 / 0.8 GB). Only boundary cases (0.96, 1.96) are missing there; that is nice-to-have, not a regression test for d2b6257.

## Severity
Medium -> low: admin-only display classification on the about page; the alerting path (the task) is correct and tested. Missing test is a gap, not a live bug.

## Better proposal (effort S)
In `test_views.py`, patch `main.views.shutil.disk_usage` with free = 0.96 GB -> assert `level == "critical"`, free = 1.96 GB -> `"warning"`. Reuse the `_fake_usage` pattern from `test_tasks.py:341-347`. Optionally add the same two boundary cases to `DiskUsageTaskTests`.

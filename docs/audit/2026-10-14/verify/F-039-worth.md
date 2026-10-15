# F-039 (worth): Disk threshold fix (d2b6257) has no regression test; view test reads real disk

**Verdict:** CONFIRMED (partly: the task half of the proposal is not needed)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- d2b6257 changed only `django/main/views.py` and `.env.example`, and added no test (`git show d2b6257 --stat`).
- `_get_disk_info` (views.py:240-261) now compares the unrounded `free_raw_gb` against the thresholds (views.py:248-250).
- `test_about_shows_disk_info_for_staff` (test_views.py:632-647) does not patch `shutil.disk_usage`. It reads the real `/` and only checks that the keys exist and that `level` is one of the three values. If the fix were reverted, the test would still pass, so it catches no regression.
- The task half of the proposal is not worth doing. `check_disk_usage_task` (tasks.py:202-210) never rounded, so it never had this bug. It is already tested with a patched `disk_usage` at 0.8, 1.5 and 5.0 GB (test_tasks.py:341-374).
- Severity is overstated. The bug only affects an admin-only label on the about page: free space from 0.95 to just under 1.0 GB showed "warning" instead of "critical". The Celery alert path was never affected. It is not a real bug or security gap, so it is low, not medium.

## Better proposal (smallest diff)
Patch `main.views.shutil.disk_usage` in the existing view test, or add one test beside it, using the same namedtuple helper as test_tasks.py:342-347. Assert that 0.96 GB free gives `level == "critical"`. Optionally assert that 1.96 GB gives "warning". This also stops the test from depending on the real disk of the host or CI runner. Leave the task tests as they are.

Effort: S.

# F-093: Disk check implemented twice (view and task)

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low (simplification, no current bug)

## Reasoning
- `django/main/views.py:240-261` `_get_disk_info()` calls `shutil.disk_usage("/")` and classifies critical/warning/ok via `DISK_CRITICAL_GB`/`DISK_WARNING_GB` (imported from tasks, views.py:25-26). Called at views.py:141.
- `django/main/tasks.py:202-233` `check_disk_usage_task()` repeats `shutil.disk_usage("/")` plus the same two-threshold if/elif/else.
- Thresholds are already shared (tasks.py:20-21), so only the GB conversion and 3-way branch are duplicated (~6 lines).
- Drift claim holds: commit d2b6257 changed only views.py to compare the unrounded value; before that the view compared rounded `free_gb` while the task compared raw. At HEAD both compare raw values, so they agree today.

## Better proposal
Minimal: add `disk_level(free_gb) -> "critical"|"warning"|"ok"` in tasks.py next to the thresholds; use it in both places. Keep the task's per-level status/log mapping as is. Value is small; do it only when touching this code.

# F-077 - last_success_at is cleared on every failure (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- Every non-success branch sets `last_success_at = None`:
  - `django/main/tasks.py:74` (sync partial), `:84` (sync failure)
  - `django/main/tasks.py:123` (heatmap, no token), `:149` (heatmap fetch error)
  - `django/main/tasks.py:216` (disk critical), `:224` (disk warning / partial)
- Symmetrically every success branch sets `last_failure_at = None` (`tasks.py:70`, `:174`, `:233`).
- These fields are persisted (`update_fields` includes both) on `TaskExecutionStatus` (`models.py:135-136`), the per-task "latest snapshot" row.
- `about.html:225-230` renders "Last success: -" when the field is None, so after one failure the admin loses when the task last worked. Both timestamps then carry no more information than `last_status` + `last_run_at`.
- Behaviour is deliberate, not accidental: tests pin it - `django/main/tests/test_tasks.py:189`, `:231`, `:331` (`test_*_clears_success_timestamp_after_*`). Still a semantic defect: the field name promises "time of last success".
- Mitigation: `TaskExecutionLog` rows keep the old timestamps and the about page lists the last 30 logs (`views.py:320`), so the info is not lost, just buried; with 3 tasks (hourly heatmap, disk check) a success can scroll out of 30 rows quickly.
- No data loss, no security impact -> low is correct.

## Better proposal
Delete the six `last_success_at = None` lines and the three `last_failure_at = None` lines (net -9 lines). Flip the three tests (`test_tasks.py:189,231,331`) to assert the seeded timestamp is preserved. Effort S.

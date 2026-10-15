# F-030 — Task status bookkeeping copy-pasted ~5x plus a redundant no-token branch

**Lens:** worth
**Verdict:** CONFIRMED (with adjustments)
**Confidence:** high
**Adjusted severity:** low (pure simplification, no behavioural defect)

## Reasoning
- Duplication is real: identical 8-field `update_fields` save + `_log_task_execution` at
  django/main/tasks.py:90-102, 129-141, 155-167, 179-191, 235-247 (5 copies, 3 tasks).
- Token pre-check is redundant: tasks.py:119-143 produces exactly what the error branch
  (145-169) produces, because `fetch_heatmap_data` returns `(None, "Heatmap is not configured.")`
  when no token (heatmap.py:77-79). Same message, same `update_snapshot_error`, same status fields,
  same `_maybe_schedule_next_refresh`, same return shape. Deleting it is behaviour-preserving.
- `failed_results`/`last_error` built twice in the `elif`/`else` at tasks.py:72-89; can be computed once.
- No deliberate decision against this found: git log for tasks.py (667e27f, 983ed1f, ...) shows no
  rationale for the duplication.

## Corrections to the finding
- Risk is understated: removing the pre-check also removes the `get_configured_github_token` import
  from tasks.py, and four tests patch `main.tasks.get_configured_github_token`
  (django/main/tests/test_tasks.py:235, 267, 294, 317). `patch` on a missing attribute raises
  AttributeError, so those tests must change. Lines 294/317 should switch to
  `@override_settings(GITHUB_HEATMAP_TOKEN="")` (or patch `main.heatmap.get_configured_github_token`);
  235/267 can just drop the patch since `fetch_heatmap_data` is mocked.
- "About -90 lines" is optimistic; realistic net is ~-60 to -70 in tasks.py.
- Severity medium overstates it; per rubric this is "low = simplification".

## Better proposal (smallest diff)
1. Helper that sets counts/status, derives timestamps from status, saves, logs:
   `_finish(status, state, total, updated, error="")` -> sets `last_success_at`/`last_failure_at`
   from `state == SUCCESS`, saves the 8 fields, calls `_log_task_execution`. Use in all 5 sites.
2. Delete tasks.py:119-143 and the `get_configured_github_token` import; adjust the 4 tests above.
3. Compute `last_error` once for any `failed_count > 0` case.

Effort: S.

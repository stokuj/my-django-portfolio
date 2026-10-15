# F-030 — Task status bookkeeping copy-pasted ~5x plus a redundant no-token branch

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (pure simplification, no behavioural defect)

## Reasoning
- Same 8-item `status.save(update_fields=[...])` + `_log_task_execution(status)` block appears 5 times: `django/main/tasks.py:90-102`, `:129-141`, `:155-167`, `:179-191`, `:235-247`. Field assignments (status / success_at / failure_at / total / updated / failed / error) are repeated in each branch.
- No-token branch `tasks.py:119-143` is functionally identical to the error branch `tasks.py:145-169`: `fetch_heatmap_data()` called with no arg falls back to `get_configured_github_token()` and returns `(None, "Heatmap is not configured.")` (`django/main/heatmap.py:77-79`). Same message, same `update_snapshot_error`, same status fields, same return shape, same `_maybe_schedule_next_refresh`.
- `failed_results` list comprehension and `last_error` join duplicated at `tasks.py:76-80` and `:82-89`.
- "Three tasks" is correct: sync, heatmap refresh, disk usage all write status (healthcheck does not).

## Caveats the finding misses
- Deleting the pre-check breaks two tests that patch `main.tasks.get_configured_github_token` (`django/main/tests/test_tasks.py:294`, `:317`): once the import is removed, `patch` raises AttributeError. They must be re-pointed to `main.heatmap.get_configured_github_token`; otherwise they'd hit the real env token / network.
- "-90 lines" is optimistic; net is closer to -60/-70 after adding the helper.
- Severity rubric puts simplification at low, not medium.

## Better proposal
One helper `_record(status, state, total, updated, failed, error="")` that sets the 7 fields (success_at/failure_at derived from `state`), saves with the existing `update_fields`, and calls `_log_task_execution`. Drop `tasks.py:119-143` and the `get_configured_github_token` import; re-point the two no-token tests to `main.heatmap.get_configured_github_token`. Compute `failed_results`/`last_error` once before the if/elif. Effort S.

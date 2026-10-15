# F-031 — Task failure branches and blog_slug filter not covered

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning

All three gaps exist at HEAD:

1. **Heatmap fetch-error branch** (`django/main/tasks.py:145-169`). Heatmap tests in `django/main/tests/test_tasks.py:234-335` cover only success (`:236`, `:268`, where `fetch_heatmap_data` returns a payload) and missing token (`:294`, `:317`, `get_configured_github_token` returns None, so the task returns at `tasks.py:143` before the fetch). No test has `fetch_heatmap_data` return an error.
2. **Sync exception branch** (`tasks.py:45-57`, `reason="task_exception"`). No test in `test_tasks.py` makes `sync_project_markdown` raise. Every mock returns a dict (`:32`, `:67`, `:106-118`, `:151`, `:179`, `:213-225`). Nothing in `django/main/tests/` matches `task_exception`, `raise` or `Exception`.
3. **blog_slug filter** (`tasks.py:37-38`). Every call is `sync_project_markdowns_task()` with no arguments. The view path (`views.py:426-429`) is tested only with `.delay` mocked (`test_views.py:542-603`, e.g. `:551 assert_called_once_with(blog_slug=None)`), so the filter never runs in a test.

## Why severity is lowered

- Branch 1 is a near copy of the missing-token branch (`tasks.py:119-143`), which is tested and asserts FAILURE, last_error and a log row. That leaves `update_snapshot_error(error)` with a dynamic message as the only untested part. The duplication also shows up as a simplification smell.
- Branch 2 maps a raised exception to a dict with `updated=False`. After that it follows the same aggregation path as the tested `download_failed` case.
- Branch 3 is a single `.filter()` line.

This is useful coverage for low regression risk. It is not a real bug or a security gap.

## Better proposal

Keep it to three small tests in `test_tasks.py`. The first two follow the existing patterns:
- `@patch fetch_heatmap_data return_value=(None, "boom")` plus a token. Assert FAILURE, `last_error == "boom"`, one TaskExecutionLog row, and `HeatmapSnapshot.last_error == "boom"`.
- `patch sync_project_markdown side_effect=RuntimeError("x")`. Assert FAILURE and that `"task_exception"` is in `last_error`.
- Two blog projects, then `sync_project_markdowns_task(blog_slug="a")`. Assert the mock was called once with project "a" and `result["total"] == 1`.

Optional: fold the duplicated failure blocks at `tasks.py:119-143` and `:145-169` into one helper. That would let a single test cover both.

Effort: S.

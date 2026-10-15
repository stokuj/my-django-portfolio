# F-031 - Task failure branches and blog_slug filter not covered (worth lens)

**Verdict:** CONFIRMED (gaps are real); severity overstated
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/tasks.py:37-38` blog_slug filter: no test in `django/main/tests/test_tasks.py` calls the task with `blog_slug`. `test_views.py:551` only asserts `delay(blog_slug=None)` on a mock, so the filter itself is never exercised.
- `django/main/tasks.py:45-57` exception branch (`task_exception`): every sync test patches `sync_project_markdown` with a return value or a non-raising side_effect (`test_tasks.py:65-75, 106-121, 213-228`). The per-project isolation (one exception must not abort the batch) is untested. This is the most valuable of the three.
- `django/main/tasks.py:145-169` fetch-error branch: heatmap tests cover success (`:235`, `:267`) and missing token (`:294`, `:317`), never `fetch_heatmap_data` returning an error. However this branch is a copy of the tested missing-token branch (`:119-143`), so the regression risk is small.
- Nothing in the proposal contradicts a documented decision; tests only, no runtime risk.

## Why low, not medium
No bug is shown; these are small, low-risk branches, and one of them mirrors code that is already tested. They are cheap to add, but they do not belong in "should fix".

## Better proposal
- Add two short tests to `test_tasks.py`, following the existing `patch` style: (1) `side_effect=RuntimeError` on one of two projects, then assert PARTIAL_SUCCESS and `reason == "task_exception"`; (2) call with `blog_slug="a"` and two blog projects, then assert `sync_project_markdown` was called once.
- For the heatmap fetch error, either add a third short test with `fetch_heatmap_data` returning `(None, "x")`, or later fold the two duplicated failure blocks (`:119-143`, `:146-169`) into one path so the existing missing-token test covers both. Doing that refactor just to get coverage is out of scope.

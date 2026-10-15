# F-076 (reproduce): Single-slug or empty runs overwrite global markdown status as SUCCESS

**Verdict:** CONFIRMED (the mechanism is real, but hard to reach)
**Confidence:** medium
**Adjusted severity:** low

## Reasoning
- `django/main/tasks.py:31-33`: there is one `TaskExecutionStatus` row, keyed only by `task_name`, whatever `blog_slug` is.
- `tasks.py:37-38`: `blog_slug` narrows the queryset. If no project matches, `results` is empty.
- `tasks.py:63,68-72`: `failed_count = 0 - 0 = 0`, so the status becomes SUCCESS, `last_failure_at` is set to None and `last_error` is cleared. A single-slug run that succeeds does the same thing, so the failures from the previous full run are wiped. Confirmed exactly as the finding describes.

## How reachable it is (this lowers the impact)
- The only caller that passes a slug is `django/main/views.py:426-429` (`run_markdown_sync_task`, staff only, POST).
- The only form in the UI, `django/main/templates/pages/about.html:186-190`, has no `blog_slug` input. It sends only `next`, so `blog_slug=None`. The test at `django/main/tests/test_views.py:551` asserts `delay(blog_slug=None)`.
- Beat (`django/config/settings.py:220-223`) calls the task with no kwargs.
- So the single-slug path needs a hand-crafted staff POST or a shell call. The empty case on a full run (0 blog projects) means there was nothing to sync, so SUCCESS there is arguably correct.

## Better proposal
No UI sends `blog_slug`, so it is dead flexibility. Remove the parameter from the task (`tasks.py:30,37-38`) and the view (`views.py:426,433-437`), and update the test. That fixes the bug at its source. If the parameter must stay, skip the status update when `blog_slug` is set. Leave "total 0 means SUCCESS" alone for full runs. Effort: S.

# F-033 (reproduce lens): Dead self-rescheduling path (schedule_next, _schedule_next_heatmap_refresh)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (dead code, no runtime impact)

## Reasoning
- `django/main/tasks.py:113` `refresh_portfolio_heatmap_cache_task(schedule_next=False)` calls `_maybe_schedule_next_refresh(schedule_next)` at :142, :168, :192.
- `django/main/tasks.py:250-257` returns early unless `schedule_next` is truthy; only then does it enqueue with `schedule_next=True` (self-chain, countdown 3600).
- Every caller in the repo passes False or nothing: beat `django/config/settings.py:218` (`{"schedule_next": False}`), admin view `django/main/views.py:452` (`delay(schedule_next=False)`), tests `django/main/tests/test_tasks.py:248,287,298,328` (no arg). A repo-wide grep (excluding lockfiles/docs) finds no other caller and no `schedule_next=True` producer except the dead branch itself.
- `django/main/views.py:189-197` `_schedule_next_heatmap_refresh` has zero references; it wraps `apply_async` in `except Exception: return`.
- `django/main/tests/test_views.py:240,278` patches `main.views...apply_async` and asserts not called. Since no live code in views calls `apply_async`, the assertion is vacuous (at most a weak regression guard).
- Small nuance: the dead view helper passes `schedule_next=False`, so if called it would add one extra run, not a self-chain. The self-chain (double-scheduling with beat) only applies to `_maybe_schedule_next_refresh` with True.

## Proposal (agree, minor tweak)
Delete `_schedule_next_heatmap_refresh` (views.py:189-197), `_maybe_schedule_next_refresh` (tasks.py:250-257) and its three calls, the beat `kwargs` (settings.py:218), and the `apply_async` patch/assert in test_views.py:240,243,278; update test_views.py:70 and :203.
Keep the task signature tolerant for one release (`def refresh_portfolio_heatmap_cache_task(**_kwargs)` or keep `schedule_next=False` unused) so already-queued messages with that kwarg do not raise TypeError. Effort S.

# F-033 — Dead self-rescheduling path (schedule_next, _schedule_next_heatmap_refresh)

**Verdict:** CONFIRMED (worth doing)
**Confidence:** high
**Adjusted severity:** low (dead code, no runtime impact)

## Reasoning
- `refresh_portfolio_heatmap_cache_task(schedule_next=False)` (django/main/tasks.py:113) only passes the flag to `_maybe_schedule_next_refresh` (tasks.py:142,168,192), which returns immediately unless truthy (tasks.py:250-257).
- All callers pass `False`: beat kwargs (django/config/settings.py:218), admin trigger `.delay(schedule_next=False)` (django/main/views.py:452). The only `True` is inside the dead branch itself (tasks.py:255).
- `views._schedule_next_heatmap_refresh` (views.py:189-197) has zero callers (grep over django/). It swallows all exceptions.
- `test_views.py:240,278` patches `main.views...apply_async` and asserts not called; views never call apply_async on that path, so the assertion is vacuous.
- History: self-scheduling came from the original plan (docs/superpowers/plans/2026-05-08-issue-51-heatmap-migration.md:461,534,549); hourly beat (settings.py:215-219) superseded it. No doc or commit says the old path is kept on purpose. Commit 667e27f ("dead code") missed it.

## Notes on proposal
- Correct and minimal: drop the param, both helpers, beat `kwargs`, the `apply_async` patch, and the asserts at test_views.py:70 and 203 (`assert_called_once_with()`).
- Risk overstated: beat enqueues with no countdown and deploys restart worker+beat together, so an in-flight message carrying `schedule_next` is unlikely. At worst one hourly run fails with TypeError and the next one succeeds. `**_kwargs` shim not needed.
- Leave the historical plan doc unchanged.

## Better proposal
Same as proposed, without the compatibility shim. Effort S.

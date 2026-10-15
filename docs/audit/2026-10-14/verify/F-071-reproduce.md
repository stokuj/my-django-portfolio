# F-071 - Redundant queries in visitor middleware and snapshot updates

**Lens:** reproduce
**Verdict:** CONFIRMED (technically accurate, negligible impact)
**Confidence:** high
**Adjusted severity:** low (bordering on won't-fix)

## Reasoning

- Middleware: `django/main/middleware.py:15-16` calls `PageView.get_instance()` (`django/main/models.py:114`, `get_or_create(id=1)` = SELECT) then `filter(id=counter.id).update(F("count")+1)` = UPDATE. Two queries where one would do. Cited line 10 is `__init__`; the real code is lines 15-16.
  - Frequency: only on `/` or `/home/` and only when the session lacks `has_visited` (`middleware.py:13-14`), so once per session. One extra PK lookup per new visitor.
- Heatmap: `about_heatmap_data` loads the snapshot (`django/main/views.py:155`), then `update_snapshot_error` (`views.py:161`) and `update_snapshot_with_payload` (`views.py:166`) each call `get_or_create_snapshot()` again (`django/main/heatmap.py:139,168` -> `heatmap.py:106`). Extra SELECT on a unique key.
  - Frequency: only when the cache is empty/stale (TTL default 60 min, plus the hourly beat refresh), so about once per hour at most.
  - The other callers (`django/main/tasks.py:121,147,171`) hold no snapshot, so the helpers' self-fetch is needed there.

## Better proposal

Leave it, or do the minimum:
- Middleware: `PageView.objects.filter(id=1).update(count=F("count") + 1)`, and only if it returns 0, call `get_instance()` and update. Saves one query per new session.
- Heatmap: add an optional `snapshot=None` parameter to both helpers (`snapshot = snapshot or get_or_create_snapshot()`) and pass it from `views.py:161,166`. Saves one query per hour.

Neither is measurable on this traffic profile; fix only if touching these files anyway.

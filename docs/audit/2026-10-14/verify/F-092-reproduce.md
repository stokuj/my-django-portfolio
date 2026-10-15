# F-092 - _calculate_last_30_days_total defensively re-parses our own payload

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (simplification)

## Reasoning
- `django/main/views.py:200-237`: 38 lines of `isinstance` checks, `try/except/continue`, `"T"` split and a `contribution_count` fallback.
- Sole caller: `_build_heatmap_snapshot_response` (`views.py:173`), reading `snapshot.payload`.
- Sole writer of `snapshot.payload`: `update_snapshot_with_payload` (`heatmap.py:140`), fed only by `fetch_heatmap_data` (`views.py:158`, `tasks.py:145`), which returns `{"username", "total", "weeks"}` (`heatmap.py:95-99`) built by `build_weeks_payload` (`heatmap.py:32-65`).
- `build_weeks_payload` already validates input (`heatmap.py:41-47`) and emits days as `{"date": isoformat(), "weekday", "count": int, "level"}` (`heatmap.py:52-57`). So the date never carries a `T`, `count` is always an int, and `contribution_count` is never written anywhere (grep: only `views.py:231`).
- Only other shape: model default `{}` (`models.py:227`), handled by `payload.get("weeks", [])`.
- Tests (`tests/test_views.py:215-275`) use the same `weeks/days/date/count` shape, so they keep passing.

## Better proposal
Keep the upper bound (the proposed one-liner drops `<= today`, and server-UTC vs GitHub user timezone can leave a "tomorrow" cell):

```python
def _calculate_last_30_days_total(payload):
    today = date.today()
    start = today - timedelta(days=29)
    return sum(
        d["count"]
        for w in payload.get("weeks", [])
        for d in w["days"]
        if start <= date.fromisoformat(d["date"]) <= today
    )
```

Do NOT move it into `build_weeks_payload`: the snapshot is cached and served stale on fetch errors (`views.py:160-163`), so a precomputed 30-day total would drift as `today` moves. Compute at read time.
Effort: S.

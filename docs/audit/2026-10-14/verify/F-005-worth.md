# F-005 - Public heatmap endpoint fetches GitHub synchronously with no backoff after errors

**Verdict:** CONFIRMED (core issue), with corrections
**Confidence:** high
**Adjusted severity:** medium (was high)

## Reasoning
- Confirmed: `about_heatmap_data` (django/main/views.py:146-167) is anonymous (`@require_GET` only) and calls `fetch_heatmap_data()` inline whenever the payload is empty or stale.
- Confirmed: `update_snapshot_error` (django/main/heatmap.py:159-171) saves only `last_error` and leaves `fetched_at` unchanged, so `is_snapshot_stale` (heatmap.py:111-126) stays True. During an outage every request fetches again. There is no lock.
- Confirmed: gunicorn runs with defaults (infra/docker-compose.prod.yml:46): 1 sync worker and a 30s timeout. REST `timeout=15` (github_client.py:55) plus GraphQL `timeout=20` (github_client.py:121) can exceed 30s on a slow upstream.
- Overstated: with a bad or revoked token, `/user` returns 401 quickly (github_client.py:59-60), so there is no worker stall and no rate limit to burn. The stall only happens on a slow or hung upstream. This is a self-DoS on a personal site that needs an upstream incident to trigger. That makes it medium, not high, and more ops/perf than security.
- Incorrect: "the stale-success branch is untested". `test_about_heatmap_data_serves_cached_snapshot_when_refresh_fails` (django/main/tests/test_views.py:281-300) covers it. Only the 503 branch has no test (`grep 503` in tests finds nothing).
- The TTL/beat race is minor. Beat runs at `crontab(minute=0)` (settings.py:215-218) and the TTL is 60 min (settings.py:173), so the window is the few seconds before beat finishes.
- Duplication with the task (tasks.py:113-198) is real but small: the view only repeats fetch, update_error, update_payload.

## Problems with the proposal
- It drops the inline fetch entirely. The heatmap is then empty after a fresh deploy for up to 1h, which is a user-visible regression the finding itself lists as a risk.
- Enqueueing `.delay()` on stale duplicates beat, which already refreshes hourly. It adds a moving part for no gain.
- No `CACHES` is configured (settings.py), so `cache.add` uses per-process LocMemCache. That is fine with 1 worker but not a global lock. Acceptable, just say so.

## Better proposal (smallest diff)
In views.py:157, serve stale data as-is and fetch inline only for the bootstrap case, behind a short lock:

```python
if not snapshot.payload:
    if not cache.add("heatmap-inline-fetch", 1, 300):  # ponytail: per-process LocMem lock
        return JsonResponse({"error": "Heatmap is loading."}, status=503)
    payload, error = fetch_heatmap_data()
    ...
```

Beat keeps stale data fresh. There is no migration, no new task call, and the deploy bootstrap still works.
Tests: add one 503 test (no snapshot, failing fetch), and one asserting a stale snapshot is served without calling `fetch_heatmap_data`. Add `cache.clear()` in setUp. The existing test at test_views.py:281 must change to `fetch_mock.assert_not_called()`.

Side note: `_schedule_next_heatmap_refresh` (views.py:189) has no callers (dead code). Mention it only, do not delete it.

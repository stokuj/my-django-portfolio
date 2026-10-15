# F-005: Public heatmap endpoint fetches GitHub synchronously with no backoff after errors

- Lens: reproduce
- Verdict: CONFIRMED (core claim), with corrections
- Confidence: high
- Adjusted severity: medium (original: high)

## Reasoning

Confirmed at HEAD:
- `django/main/urls.py:8` routes `about/heatmap-data/` to `about_heatmap_data` with no auth. `about.html:433` calls it on every about-page load.
- `views.py:157-166`: when `not snapshot.payload or is_snapshot_stale(snapshot)`, the view calls `fetch_heatmap_data()` inline. There is no lock and no rate limiting; grep finds no throttle in code or Caddy.
- `fetch_heatmap_data` (`heatmap.py:68-99`) does REST `/user` (timeout=15, `github_client.py:55`) and then GraphQL (timeout=20, `github_client.py:121`).
- `update_snapshot_error` (`heatmap.py:159-171`) saves only `last_error`, not `fetched_at`. So `is_snapshot_stale` (`heatmap.py:111-127`) stays True, and every later request refetches while upstream keeps failing. N requests make N fetches.
- Gunicorn runs with defaults (`infra/docker-compose.prod.yml:46`, with no `-w` or `--timeout`, no gunicorn config, and no WEB_CONCURRENCY): 1 sync worker and a 30s timeout. If GitHub hangs, one request can block the only worker for up to about 35s and gets killed by the gunicorn timeout.
- The TTL is 60 min (`settings.py:173`) and beat runs at `crontab(minute=0)` (`settings.py:215-218`). Staleness uses `<=`, so visitors near :00 race beat.
- The view duplicates the fetch/update/error sequence of `refresh_portfolio_heatmap_cache_task` (`tasks.py:111-198`).

Corrections:
- "The stale-success branch is untested" is false. `test_views.py:281-303` (`test_about_heatmap_data_serves_cached_snapshot_when_refresh_fails`) covers it. Only the 503 branch (`views.py:166`) has no test.
- The impact is conditional. Amplification needs a stale snapshot plus a failing upstream. With a bad token, GitHub returns 401 quickly (no worker pinning, and no token quota to burn). Worker pinning needs GitHub to hang, not just fail. When upstream is healthy, the single sync worker serializes requests, so the first success makes the snapshot fresh and stops the stampede. That makes this an anonymous-triggerable availability degradation during outages, not a directly exploitable issue, so medium.

## Better proposal

Same direction as the original, kept minimal:
1. In `about_heatmap_data`, never fetch inline. Return the snapshot if it has a payload, otherwise return 503.
2. If the snapshot is stale, call `if cache.add("heatmap-refresh-lock", 1, 300): refresh_portfolio_heatmap_cache_task.delay()` and wrap the enqueue in try/except, as `_schedule_next_heatmap_refresh` does at `views.py:189-196`. Note that CACHES is not configured, so this is a per-process LocMemCache lock. That is acceptable with 1 worker; use the Redis cache that is already present if workers increase.
3. Tests: no payload gives 503 and no inline fetch. Repeated GETs on a stale snapshot do not call `fetch_heatmap_data`, and enqueue at most once. Update `test_about_heatmap_data_fetches_sync_when_cache_missing` (`test_views.py:241`).

Effort: S.

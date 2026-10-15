# F-005 (risk lens): Public heatmap endpoint fetches GitHub synchronously with no backoff after errors

**Verdict:** CONFIRMED (mechanism), severity overstated
**Confidence:** high
**Adjusted severity:** medium (category: performance/ops rather than security)

## What holds
- `django/main/views.py:157-166`: anonymous `about_heatmap_data` calls `fetch_heatmap_data()` inline whenever payload is empty or stale.
- `django/main/heatmap.py:159-171`: `update_snapshot_error` saves only `last_error`, `fetched_at` is not advanced, so while upstream keeps failing every request refetches. There is no lock or throttle.
- `django/main/github_client.py:55,121`: timeouts are 15s and 20s, run one after the other (`heatmap.py:82,88`).
- `infra/docker-compose.prod.yml:46`: `gunicorn config.wsgi:application --bind 0.0.0.0:8000` uses the defaults (1 sync worker, 30s timeout).
- `settings.py:173,215-218`: TTL is 60 min and beat runs at `crontab(minute=0)`, so there is a short race window each hour.

## Why it is not high/security
- An attacker cannot force the stale state. The inline fetch only fires when beat has already failed to refresh (GitHub outage, expired token) or in the seconds-long race after each hour.
- A bad or expired token fails fast with a 401 (`GitHubAuthError`, `heatmap.py:90`). The long hang only happens when GitHub is slow, not when it is down or rejecting the token.
- A single sync gunicorn worker can be tied up by any request flood. This endpoint makes that worse during outages, but it is not a separate exploit.

## Factual errors in the finding
- "stale-success branch untested" is wrong. `django/main/tests/test_views.py:281-302` (`test_about_heatmap_data_serves_cached_snapshot_when_refresh_fails`) covers it. Only the 503 branch has no test.
- The test-impact list is incomplete. That same test asserts `fetch_mock.assert_called_once_with()` (line 302), so it also breaks under the fix, along with `test_about_heatmap_data_fetches_sync_when_cache_missing` (line 242).

## Risks of the proposed fix
1. **No `CACHES` setting** (grep of `settings.py`), so the default is LocMemCache, one per process. `cache.add` is only a per-gunicorn-process lock. That is fine with 1 worker, but it stops deduplicating once workers are added (the F-009 fix). Use Django's built-in `RedisCache` on the existing redis, or accept the limit and say so in a `ponytail:` comment.
2. **Broker down means a 500 on the public page.** `.delay()` raises when redis is unreachable, and kombu's publish retry can also block for a few seconds. Wrap it in try/except the way `_schedule_next_heatmap_refresh` does (`views.py:189-197`).
3. **Cold start.** The proposal says to enqueue only "if stale". The empty-payload case (`fetched_at=None`, which counts as stale per `heatmap.py:122`) must also enqueue. Otherwise the heatmap stays on 503 for up to 59 minutes after a fresh deploy or DB reset, until beat fires.
4. **503 message.** The frontend shows the error text in a red alert (`about.html:57-58`). A "warming up" message is better than a raw upstream error on a first visit.
5. **Duplicated refresh logic.** Once the inline fetch is removed, `views.py` no longer duplicates `tasks.py:113-198`. No migration is needed and no API shape changes.

## Better proposal
In the view, keep serving whatever snapshot exists. If the payload is missing or stale, run:
`if cache.add("heatmap-refresh-lock", 1, 300): try: refresh_portfolio_heatmap_cache_task.delay() except Exception: pass`
Return 503 only when there is no payload. Rewrite the two tests above and add a test where 5 GETs with a stale snapshot give 0 fetches and 1 enqueue. Add `cache.clear()` in `ViewsTest.setUp`.
Unrelated, spotted while reading: `_schedule_next_heatmap_refresh` (`views.py:189`) has no callers (dead code).

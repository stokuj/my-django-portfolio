# F-068 — Unused override params, re-defaulted settings, redundant login re-validation

- Lens: reproduce
- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low (simplification, effort S)

## Reasoning

All four sub-claims hold at HEAD:

1. Unused override parameters (no caller, including tests, passes them):
   - `fetch_heatmap_data(github_token=None)` (django/main/heatmap.py:68,77). Callers: views.py:158, tasks.py:145, test_heatmap.py:185,231,246 - all call with no args.
   - `is_snapshot_stale(snapshot, ttl_minutes=None)` (heatmap.py:111,121). Only caller views.py:157 passes `snapshot` only.
   - `fetch_contribution_days(..., graphql_url=...)` (github_client.py:80-84,108). Callers heatmap.py:88, test_heatmap.py:76,92,111 never pass it.
   - `sync_project_markdown(project, timeout=20)` (markdown_sync.py:135). Callers tasks.py:44, test_markdown_sync.py:64,91,118 never pass `timeout`. `_download_markdown(url, timeout=20)` (markdown_sync.py:99) only receives it from line 151, so the default there is also dead.
2. Re-defaulted settings: `settings.py:172` defines `GITHUB_HEATMAP_TOKEN = env(..., default="").strip()` and `:173` defines `HEATMAP_CACHE_TTL_MINUTES = env.int(..., default=60)`. heatmap.py:15 repeats `getattr(..., "")`, `or ""` and `.strip()`; heatmap.py:121 repeats `getattr(..., 60)` and `int(...)`. Tests only use `override_settings` with plain strings (test_heatmap.py:170,228,236), so direct `settings.X` stays safe.
3. Redundant login check: `fetch_authenticated_user` already raises `GitHubUpstreamError` unless `login` is a non-empty `str` (github_client.py:72-77). heatmap.py:83-86 checks the same thing again. Test mocks always return a valid `login` (test_heatmap.py:178,244).

Removing the parameters changes no runtime behavior: every call site already takes the settings path.

## Better proposal

As proposed, plus also drop the `timeout` param from `_download_markdown` (markdown_sync.py:99) or make it a module constant. Keep `get_configured_github_token()` as a thin helper (tests patch it in views/tasks), just make its body `return settings.GITHUB_HEATMAP_TOKEN or None`.

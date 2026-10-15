# F-088 — Redundant legacy assertions and weak status checks (reproduce)

**Verdict:** CONFIRMED (with corrections)
**Confidence:** high
**Adjusted severity:** low

## Reasoning

- Legacy guards exist in `django/main/tests/test_views.py`: `:83` ("Heatmap Refresh (FastAPI)"), `:104-109` ("Connect your GitHub account", "/accounts/3rdparty/", "/accounts/github/login/", "Disconnect GitHub", "Live from FastAPI", "Heatmap Refresh (FastAPI)"), `:211-213` ("Login with GitHub", "Live from FastAPI", "(FastAPI)").
- **Wrong line refs for test_urls.py:** the file has 63 lines; the cited `315-316, 322-346` do not exist. The real legacy guards are `django/main/tests/test_urls.py:32-33` (negative string asserts), `:39-41` (heatmap-disconnect 404), `:57-63` (`/accounts/login/`, `/accounts/3rdparty/` 404).
- Settings checks in `ViewsTest` (`test_views.py:25`): only **one** test uses the `test_task_3_*` name (`:58-61`). The second (`:63-70`, `test_heatmap_refresh_is_scheduled_hourly_via_celery_beat`) already has a descriptive name. Claim "names" (plural) is overstated.
- `test_urls.py:35-37` asserts only `!= 302`. Worse than stated: no token is configured in that test, so `about_heatmap_data` (`views.py:149-153`) returns 404 "Heatmap is not configured." The test passes on a 404 and does not show the endpoint is public with data. The configured path is covered elsewhere (`test_views.py:215` `test_about_heatmap_data_returns_public_admin_data`).

## Corrections to the proposal

- Do not blindly delete the route-removal 404 tests (`test_urls.py:39-41, 57-63`). They are cheap, fast, and guard against re-adding allauth/disconnect routes. Keep them or collapse into one loop with `subTest`.
- The negative string asserts on removed UI ("FastAPI", "Disconnect GitHub", etc.) are low value and can go.

## Better proposal

1. Remove the negative `assertNotContains` lines for FastAPI/GitHub-login strings in `test_views.py:83,104-109,211-213` and `test_urls.py:32-33`.
2. Rename `test_task_3_settings_...` to `test_settings_drop_sites_framework_and_heatmap_api_base_url`; optionally move it plus the beat test into a `SettingsTest` class.
3. `test_urls.py:35-37`: assert `status_code == 404` with the "not configured" JSON (or patch the token and assert 200), not `!= 302`.

Effort: S.

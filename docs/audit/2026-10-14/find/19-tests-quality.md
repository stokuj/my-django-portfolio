# tests-quality

Scope: `django/main/tests/`, `tests/`, and the CI/Makefile wiring that runs them (HEAD of `dev`). Read-only.

## 1. Django test suite never runs in `make verify` / CI
- Severity: high | Category: ci | File: Makefile:38 | Effort: S
- Problem: `make verify` runs `python django/manage.py test` from the repo root with no label. `django/` has no `__init__.py`, so discovery from `.` finds only the `tests/` package. Checked with `DiscoverRunner.build_suite([])` from the repo root: 26 tests (all in `tests.test_operational_*`). From `django/`: 96. So none of the 96 tests in `django/main/tests/` run in CI, and CI stays green when they fail. CLAUDE.md also documents `uv run python -m pytest tests/`, but pytest is not a dependency (pyproject.toml:24-27).
- Proposal: change the Makefile line to `... manage.py test main tests`. Checked: that discovers 122 tests from the repo root. Fix the CLAUDE.md command to match.
- Risk: tests that are currently broken but silent may start failing CI after the fix. Run them once locally first.

## 2. "Heatmap disabled" tests always pass and depend on the local `.env`
- Severity: medium | Category: tests | File: django/main/tests/test_views.py:77 | Effort: S
- Problem: `test_views.py:77,85` and `test_urls.py:310` "prove" the not-configured state by asserting that the response contains `GITHUB_HEATMAP_TOKEN`. That string sits in inline JS that is always rendered (`pages/about.html:310`), so the assertion passes whether or not a token is set. The tests also read the real `settings.GITHUB_HEATMAP_TOKEN` from `.env`, and `.env.example:12` ships a non-empty placeholder. With a token in `.env` (the local `.env` has one), `test_urls.py:318` calls the real `api.github.com` and only asserts `!= 302`.
- Proposal: put `@override_settings(GITHUB_HEATMAP_TOKEN="")` on `ViewsTest` and `URLsTest`. Assert on `response.context["heatmap_enabled"]` instead of the page text. In `test_urls.py:318`, assert `status_code == 404`.
- Risk: none.

## 3. No negative tests for the markdown sanitizer (XSS boundary)
- Severity: medium | Category: security | File: django/main/views.py:357 | Effort: S
- Problem: `blog_detail` renders `blog_markdown_html|safe` (`projects/detail.html:18`). The only sanitizer tests (`test_views.py:396-436,613`) cover `<script>`, `onerror` on `<img>`, and an external img src. Nothing guards `[x](javascript:...)`, `<a href="data:...">`, `onclick`/`style` attributes, `<iframe>`/`<svg>`/`<form>`, or img `src` look-alikes such as `https://github.com.evil.tld/`. If someone later widens `ALLOWED_MARKDOWN_*` or `_clean_attributes`, nothing would fail.
- Proposal: add one table-driven `SimpleTestCase` that calls `_render_markdown_to_html` directly with these payloads and asserts each dangerous token is gone. No DB or file setup is needed.
- Risk: none.

## 4. `about_heatmap_data` failure paths untested, including a hammering risk
- Severity: medium | Category: tests | File: django/main/views.py:157 | Effort: S
- Problem: no test covers the 503 branch (no cached payload and the fetch fails, `views.py:164`), or a stale snapshot that refreshes successfully. On error, `fetched_at` is not updated (`heatmap.py:337-349`), so every anonymous request to this public endpoint calls GitHub synchronously while upstream is down. No test pins that behaviour.
- Proposal: add tests for (a) no snapshot and an error → 503, (b) a stale payload and a successful fetch → new data, (c) two requests in a row while upstream fails, asserting how many times fetch is called. (c) documents the current hammering and becomes the regression test if it gets throttled.
- Risk: none.

## 5. Task failure branches not covered
- Severity: medium | Category: tests | File: django/main/tasks.py:145 | Effort: S
- Problem: `refresh_portfolio_heatmap_cache_task` with a fetch error (`tasks.py:145-169`) is untested. Only the missing-token failure is tested (`test_tasks.py:293-333`). The `sync_project_markdowns_task` exception branch that records `task_exception` (`tasks.py:45-57`) is untested. So is the `blog_slug` filter (`tasks.py:37-38`), which the admin button uses.
- Proposal: add three tests: `fetch_heatmap_data` returns `(None, "x")` → FAILURE status, log row, and `snapshot.last_error == "x"`; `sync_project_markdown` raises → FAILURE with `task_exception` in `last_error`; `blog_slug=` syncs only the matching project.
- Risk: none.

## 6. Markdown sync filename grows on every run; the test does not catch it
- Severity: medium | Category: bug | File: django/main/markdown_sync.py:168 | Effort: S
- Problem: the target basename is taken from the current stored name. The old file still exists when the new one is saved, so storage appends a random suffix every run. Reproduced with `FileSystemStorage` (scratch dir, same save/delete order as the code): `sync-success.md` → `sync-success_oVzDuox.md` → `sync-success_oVzDuox_dGozl3E.md` → ... It grows every 2 h until it hits the 100-char `max_length` truncation. `test_markdown_sync.py:48` checks only the content, not the name, and does not check that the old file was deleted.
- Proposal: save to the canonical `f"{blog_url or f'project-{id}'}.md"`, deleting the old file first or using a storage that overwrites. Add asserts that the name is stable across two syncs and that the old file is gone.
- Risk: deleting before writing loses the old file if the write fails. Write to a temp name and swap, or accept the risk (the next sync fixes it).

## 7. Markdown download guards untested; the mock skips one of them
- Severity: medium | Category: tests | File: django/main/tests/test_markdown_sync.py:15 | Effort: S
- Problem: `_make_mock_response` always sets `headers = {}`, so the Content-Length guard (`markdown_sync.py:112-121`) never runs. Also untested: HTML-response rejection (`:130`), falling back to the next candidate after a 404 (`:149-157`), ignoring a non-GitHub `github_url` (`:49`), `no_candidate_urls` (`:137`), and `UnicodeDecodeError`.
- Proposal: add a `headers` parameter to the helper, then add one test per guard. Each is 5-10 lines.
- Risk: none.

## 8. Disk threshold fix (d2b6257) has no regression test; view test reads the real disk
- Severity: medium | Category: tests | File: django/main/tests/test_views.py:632 | Effort: S
- Problem: commit d2b6257 changed `_get_disk_info` (`views.py:240-253`) to compare against the unrounded free value, but added no test. `test_about_shows_disk_info_for_staff` calls the real `shutil.disk_usage("/")` and only checks that the keys exist and `level` is in the allowed set. That is host-dependent and would pass with the old bug. The task tests (`test_tasks.py:349-374`) use 5.0/1.5/0.8 GB and never test the boundary.
- Proposal: patch `main.views.shutil.disk_usage` and assert 0.96 GB → `critical` and 1.96 GB → `warning` (both round up past the threshold). Do the same for `check_disk_usage_task`.
- Risk: none.

## 9. Staff endpoints: authorization and error branches thin
- Severity: low | Category: tests | File: django/main/views.py:422 | Effort: S
- Problem: access control is tested only for anonymous users (`test_views.py:527`, `test_urls.py:330-338`). Missing: a logged-in non-staff user, GET → 405 (`require_POST`), the enqueue-failure branch (`views.py:430-431,453-454`), and passing `blog_slug` through. The test `Client` also skips CSRF checks, so CSRF on these POSTs is never exercised. The staff-user setup is copy-pasted about 10 times.
- Proposal: add a single `AdminToolsTests` class with a `setUpTestData` staff user and a non-staff user. Use `Client(enforce_csrf_checks=True)` for one CSRF-rejection test, and `delay` raising `Exception` for the error message.
- Risk: none.

## 10. Vacuous mock hides dead code
- Severity: low | Category: tests | File: django/main/tests/test_views.py:240 | Effort: S
- Problem: `test_about_heatmap_data_fetches_sync_when_cache_missing` patches `apply_async` and asserts it was not called, but the view never calls it. Its only caller would be `_schedule_next_heatmap_refresh` (`views.py:189-197`), which has no callers. Also, `schedule_next=True` (`tasks.py:250-257`) is never passed in production (`settings.py:218`, `views.py:452`).
- Proposal: delete `_schedule_next_heatmap_refresh` and the `apply_async` patch and assert. Consider dropping the `schedule_next` self-rescheduling, since Celery beat already schedules the task.
- Risk: none.

## 11. GitHub client and heatmap error mapping partly untested
- Severity: low | Category: tests | File: django/main/github_client.py:57 | Effort: S
- Problem: untested: `fetch_authenticated_user` on 403, 5xx, timeout, invalid JSON, and missing fields (`github_client.py:57-75`); GraphQL errors that are not auth errors → `GitHubUpstreamError` (`:141`); `fetch_heatmap_data` mapping an upstream error to "temporarily unavailable" (`heatmap.py:270-271`) and the no-token path (`:255-257`).
- Proposal: parametrize the existing 401 test over status codes with `subTest`, and add one test for the upstream mapping.
- Risk: none.

## 12. Redundant legacy assertions and weak checks
- Severity: low | Category: tests | File: django/main/tests/test_views.py:58 | Effort: S
- Problem: many asserts guard features that were removed: "FastAPI", "Login with GitHub", `/accounts/3rdparty/`, and "Disconnect GitHub" (`test_views.py:83,104-109,211-213`; `test_urls.py:315-316,322-346`). Settings assertions live in `ViewsTest` under the ticket-style name `test_task_3_...` (`test_views.py:58-70`). `test_about_heatmap_data_is_public` asserts only `!= 302` (`test_urls.py:318-320`).
- Proposal: delete the removed-feature guards (git history keeps them). Move the settings checks to a small `SettingsTests` class with descriptive names. Assert exact status codes.
- Risk: none.

# F-097 — Staff endpoints: authorization and error branches thinly tested

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning
Endpoints: `run_markdown_sync_task` (django/main/views.py:422-445) and `run_heatmap_refresh_task` (views.py:448-461), both `@staff_member_required` + `@require_POST`, neither `csrf_exempt`; `CsrfViewMiddleware` is enabled in settings.

Existing coverage:
- Anonymous POST -> 302 to /admin/login/: test_views.py:527, test_urls.py:47, test_urls.py:52.
- Staff happy path: markdown sync with `blog_slug=None` (test_views.py:532-551), heatmap refresh (test_views.py:183-202).
- Redirect safety (`next` / external `next` / external `HTTP_REFERER`): test_views.py:553-611 (markdown sync only).

Gaps verified by grep over django/main/tests/:
- No logged-in non-staff user test (no `create_user` without `is_staff=True`).
- No GET -> 405 test for either endpoint.
- No test where `.delay` raises; the `except Exception` branches at views.py:430-431 and 453-454 are untested.
- `blog_slug` pass-through (views.py:426, 433-437) never tested with a non-empty slug; only `blog_slug=None` asserted (test_views.py:551).
- No `Client(enforce_csrf_checks=True)` anywhere.
- Staff/admin user creation is repeated 9 times in test_views.py (87, 114, 156, 186, 534, 555, 575, 595, 635); only 5 of those concern the staff endpoints, the rest are about-page tests.

## Better proposal
Prioritise the project-owned logic: (1) `delay` raising -> 302 + error message, for both views; (2) non-empty `blog_slug` -> `delay(blog_slug="x")`, including whitespace stripping. Non-staff -> 302, GET -> 405 and CSRF tests mostly re-test Django decorators/middleware; add them only as cheap one-liners. Factor staff user into `setUpTestData` for the endpoint tests only; do not churn the about-page tests.

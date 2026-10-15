# F-038 (worth): 'Heatmap disabled' tests always pass and depend on local .env

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `about.html:257-310`: the inline script containing the literal "GITHUB_HEATMAP_TOKEN" is gated only by `heatmap_component_visible`, which `views.py:134` hard-codes to `True`. So `assertContains(response, "GITHUB_HEATMAP_TOKEN")` at `test_views.py:81`, `test_views.py:103` and `test_urls.py:31` passes whether or not a token is set; it does not test the disabled state.
- `settings.py:29,172` reads `GITHUB_HEATMAP_TOKEN` from the project `.env`; no test overrides it for these classes (only `test_heatmap.py:170,228,236` use `override_settings`). The local `.env` has a non-empty token, CI's `.env` (`.github/workflows/django.yml:39-43`) does not, so results depend on the environment.
- `test_urls.py:35-37` asserts only `!= 302`. With a token, `views.py:149-158` goes to `fetch_heatmap_data()` and makes a real GitHub call (empty snapshot in the test DB). Without a token it returns 404. Both pass, so the test catches nothing and is network-dependent locally.
- Line refs in the finding are off: test_urls.py has 63 lines. The real lines are 31 and 35-37, not 310/318. The substance is unchanged.
- No docs or git log entry treats this as intentional.

## Better proposal (smallest diff)
- Add `@override_settings(GITHUB_HEATMAP_TOKEN="")` on `ViewsTest` and `URLsTest`. This is the same pattern as test_heatmap.py.
- Replace the `"GITHUB_HEATMAP_TOKEN"` string checks with `assertFalse(response.context["heatmap_enabled"])`.
- In `test_about_heatmap_data_is_public`, use `assertEqual(response.status_code, 404)`.
Effort S. Risk none.

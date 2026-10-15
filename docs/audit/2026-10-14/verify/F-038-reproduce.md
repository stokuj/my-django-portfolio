# F-038 (reproduce): 'Heatmap disabled' tests always pass and depend on local .env

**Verdict:** CONFIRMED (two cited line numbers are wrong)
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `about.html:308-310`: the string `GITHUB_HEATMAP_TOKEN` is a JS literal inside the `{% if heatmap_component_visible %}` script block. `views.py:134` always sets `heatmap_component_visible=True`. The string is rendered whether `heatmap_enabled` is true or false.
- So `assertContains(response, "GITHUB_HEATMAP_TOKEN")` at `test_views.py:81` (test at :76), `test_views.py:103` (test at :85) and `test_urls.py:31` can't tell the enabled and disabled states apart. These tests pass in both states.
- `settings.py:29` calls `env.read_env(.env)`, and `settings.py:172` reads `GITHUB_HEATMAP_TOKEN`. `read_env` uses setdefault, so the documented test command (`SECRET_KEY=test ... manage.py test`) still picks up the token from the local `.env`. The local `.env` has a non-empty `GITHUB_HEATMAP_TOKEN` line. None of the cited tests override the setting: the only `override_settings` in `ViewsTest` is for `MEDIA_ROOT` (`test_views.py:30`), and `URLsTest` has none.
- `test_urls.py:35-36` (`test_about_heatmap_data_is_public`): when a token is set, `views.py:149` lets the request through. The snapshot is empty in the test DB, so `views.py:158` calls `fetch_heatmap_data()`. That makes real HTTP calls to `api.github.com/user` and `/graphql` (`github_client.py:52-53,107`). The test only asserts `!= 302`, so 200, 404 and 503 all pass.
- Line corrections: `test_urls.py` is 63 lines long. The cited `:310` is actually `:31` and `:318` is `:35-36`. `test_views.py:77,85` is close enough: the tests start at :76 and :85.
- Where the tests run: CI (`make verify`) presumably runs without the token. There the tests are only weak, with no network calls. The real GitHub calls and the dependence on `.env` happen in local runs.

## Better proposal
- Set `GITHUB_HEATMAP_TOKEN=''` for the whole of `ViewsTest`. The simplest way is to add it to the existing `override_settings(MEDIA_ROOT=...)` at `test_views.py:30`. Add `@override_settings(GITHUB_HEATMAP_TOKEN="")` to `URLsTest`. `get_configured_github_token()` reads settings on every call, so the override takes effect.
- Replace the string assertions with `assertFalse(response.context["heatmap_enabled"])`.
- In `test_about_heatmap_data_is_public`, assert `status_code == 404` with the token unset. Or set a token and patch `main.views.fetch_heatmap_data` to cover the public 200 path without network calls.
- Effort: S. Risk: none.

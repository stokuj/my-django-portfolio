# F-040 (worth lens): Custom 500 handler hits the DB and re-implements Django defaults

**Verdict:** CONFIRMED (with adjustments)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/views.py:95-97` `handler500` calls `render(request, "errors/500.html", status=500)`, so every context processor in `django/config/settings.py:78-85` runs. Three of them query the DB: `context_processors.py:10` (`Project.objects.count()`), `:15` (`PageView...first()`), `:28` (`PortfolioProfile...first()`).
- `errors/500.html:1` extends `base.html`, which uses those values (`base.html:119,186-187,192`). If the original error is a DB outage, the handler raises again. Django does not catch errors raised inside the 500 callback, so the request falls through to Gunicorn's plain error page.
- `views.py:90-92` `handler404` matches `django.views.defaults.page_not_found` except for the `errors/` template prefix. `config/urls.py:32-34` only wires the two handlers.
- Django's default `server_error` renders `500.html` with an empty `Context` and no request, so no context processors run. The 500 template chain only needs `{% url %}`, `{% static %}` and `{% now %}` (`base.html:9-11,44-57`; `components/hero/error_500_content.html:6`), and none of those touch the DB. The handlers were added in commit c96c3b4 with no recorded reason for keeping them custom.

## Why severity drops to low
- Effect: during a DB outage, users see a plain 500 page instead of the styled one. They get an error page either way. Gunicorn still logs the original exception as `__context__` of the new one, so no information is lost.
- Nothing can be exploited and no data is lost. The custom handlers just duplicate built-in behaviour.

## Gaps in the proposal
- `django/main/tests/test_views.py:22` imports `handler404, handler500`, and `ErrorHandlersTest` (`:650-664`) calls them directly. After the change, that import fails and the whole test module stops loading. Rewrite the tests to call `django.views.defaults.page_not_found` / `server_error`, or to use `self.client` with `DEBUG=False`.
- The 500 page will show blank profile fields (`base.html:119,122-123,192` have no `|default`), and the nav and footer links go to `#`. This is acceptable, but list it as the known cost.

## Better proposal
Same as the original, plus the test fix:
1. `git mv django/main/templates/errors/{404,500}.html django/main/templates/`
2. Delete `views.py:90-97` and `config/urls.py:32-34`.
3. Update the `test_views.py:22` import and `ErrorHandlersTest` to use `django.views.defaults.page_not_found` / `server_error`.

Effort: S.

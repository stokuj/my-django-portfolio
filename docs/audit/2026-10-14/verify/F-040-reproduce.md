# F-040 — Custom 500 handler hits the DB and re-implements Django defaults

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (failure-mode bug; impact is a bare Gunicorn error page instead of the styled one, no data loss)

## Reasoning
- `django/main/views.py:95-97` — `handler500` calls `render(request, "errors/500.html", status=500)`, i.e. a RequestContext, so every context processor runs.
- `django/config/settings.py:79-81` registers `visitor_counter`, `project_count`, `portfolio_profile`; each queries the DB (`django/main/context_processors.py:10` `Project.objects.count()`, `:15` `PageView.objects.filter(...).first()`, `:25-26` `PortfolioProfile.objects.filter(...).first()`).
- `django/main/templates/errors/500.html:1` extends `base.html`, which consumes those variables (`base.html:50,64,119,186-187`).
- If the original exception is a DB outage (OperationalError), these queries raise again inside the handler. Django's `handle_uncaught_exception` does not guard the callback, so the exception propagates out of the middleware chain to the WSGI server, and Gunicorn returns its own bare 500. Reproducible as described.
- Redundancy claim holds: `config/urls.py:33-34` plus `views.py:90-97` only change the template path. Django's default `page_not_found` already renders `404.html` with the request (context processors still run, so the 404 page keeps profile data), and default `server_error` renders `500.html` with no context (no DB access).

## Notes / corrections to the proposal
- Proposal omits tests: `django/main/tests/test_views.py:22` imports `handler404, handler500` and `:650-664` (`ErrorHandlersTest`) calls them directly. Those tests must be rewritten (e.g. `django.views.defaults.server_error(request)` / client GET with `DEBUG=False` asserting "Server Error" and "Page Not Found").
- Under the default `server_error`, `base.html` still works without context: `{% url %}`/`{% static %}` need no request, variables fall back to `|default` or empty strings. Footer shows empty name/visitor count; acceptable.

## Better proposal
Move `templates/errors/404.html` -> `templates/404.html` and `errors/500.html` -> `templates/500.html`; delete `handler404`/`handler500` in `views.py:90-97` and `config/urls.py:32-34`; update `ErrorHandlersTest` (`test_views.py:22,650-664`) to exercise Django's default views. Effort S.

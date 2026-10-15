# F-089 — Duplicate URL name 'home'; reverse resolves to /home/

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/urls.py:5-6`: both `path("", ...)` and `path("home/", ...)` use `name="home"`.
- Reproduced at HEAD: `reverse('home')` returns `/home/` (Django returns the last pattern registered under a duplicate name).
- Consumers that therefore link to `/home/` instead of `/`: `base.html:44,50,55,152`, `error_404_content.html:6`, `error_500_content.html:6`, and the redirect fallback `views.py:396` (`_get_safe_redirect_url`).
- Impact is cosmetic/SEO only: both paths serve `views.home`, and the visitor counter treats both as home (`middleware.py:13`). No functional bug.

## Better proposal
Minimal fix: drop `name="home"` from line 6 (or delete the `home/` route). If `/home/` must keep working, make it `RedirectView.as_view(pattern_name="home", permanent=True)`.
Follow-ups if the route changes: `tests/test_urls.py:24` expects 200 for `/home/`, and `tests/test_middleware.py:28-30` expects `/home/` to bump the counter. With a redirect, `/home/` would also be counted by the middleware before redirecting (`middleware.py:13`). That is harmless because of the session flag, but `"/home/"` could be removed from that tuple.

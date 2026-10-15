# F-024 (worth lens): Cookieless home hits create session rows that are never purged

**Verdict:** CONFIRMED (worth fixing, but severity overstated)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/middleware.py:14,17`: any request to `/` or `/home/` without a `has_visited` session writes `request.session["has_visited"] = True`. That marks the session modified, so `SessionMiddleware` (`django/config/settings.py:59`) saves a new row on each cookieless hit.
- `SESSION_ENGINE` is never set in `django/config/settings.py`, so Django's default DB backend is used and each hit inserts a `django_session` row.
- `clearsessions` is not used anywhere in the repo. `CELERY_BEAT_SCHEDULE` (`django/config/settings.py:214-228`) has only the heatmap, markdown and disk tasks, and nothing under `infra/` runs it. Expired rows are never deleted.
- Nothing in `docs/` or `git log` shows a deliberate choice to keep sessions. The only session-related history is test changes.
- Severity: this is not data loss and is not exploitable beyond slow table growth. Each row is a few hundred bytes. Even a steady crawler only adds tens to low hundreds of MB per year. Nothing in the repo probes `/` (no healthcheck or curl in `infra/`), so the "uptime probes" part is a guess. `low` fits better than `medium`.
- The proposal is correct. `clearsessions` deletes only rows past `expire_date` (default `SESSION_COOKIE_AGE` = 2 weeks), so the table is bounded to about 2 weeks of hits. Nothing breaks.

## Better proposal (smaller, fixes the root cause)
Stop using the session for the anonymous visitor flag. Use a plain cookie in the same middleware:

```python
if is_home and not request.COOKIES.get("has_visited"):
    ...increment...
    response = self.get_response(request)
    response.set_cookie("has_visited", "1", max_age=settings.SESSION_COOKIE_AGE,
                        secure=settings.SESSION_COOKIE_SECURE, httponly=True, samesite="Lax")
    return response
```

- This is about one file and ~5 lines. It needs no new Celery task, beat entry or TaskExecutionStatus bookkeeping, and it removes the per-hit DB write instead of cleaning up after it.
- Counting semantics stay the same: once per browser per 2 weeks. The existing tests in `django/main/tests/test_middleware.py:13-33` use `Client()`, which keeps cookies, so they should still pass.
- The only rows left are admin login sessions, which are negligible. If they ever matter, add the clearsessions beat task then.
- Fallback if the session flag is kept on purpose: add a daily beat entry that calls `call_command("clearsessions")`, next to `check-disk-usage-daily`.

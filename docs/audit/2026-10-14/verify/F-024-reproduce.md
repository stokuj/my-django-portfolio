# F-024 (reproduce lens): Cookieless home hits create session rows that are never purged

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning
- `django/main/middleware.py:13-17`: on `/` or `/home/` with no `has_visited` in session, it increments `PageView` and sets `request.session["has_visited"] = True`. That marks the session modified, so `SessionMiddleware` saves it.
- `django/config/settings.py:59-60`: `SessionMiddleware` runs before `VisitorCountMiddleware`. No `SESSION_ENGINE` is set, so the default DB backend (`django_session`) is used.
- `django/config/settings.py:214-228`: `CELERY_BEAT_SCHEDULE` has only the heatmap, markdown and disk-usage tasks. `clearsessions` appears nowhere in the repo (code, infra, Makefile, CI); grep returns nothing outside docs.
- Reproduced on a scratch sqlite DB (`DB_NAME=/tmp/...`, repo DB untouched): 5 x `Client().get('/')` gave `Session.objects.count() == 5`, `PageView.count == 5`, status 200, `Vary: Cookie`, `sessionid` cookie set.

## Notes
- Growth is unbounded only because nothing purges. With the default `SESSION_COOKIE_AGE` (2 weeks), `clearsessions` would cap the table at about 2 weeks of cookieless traffic.
- Side effect, outside this finding: bots and probes also inflate the visitor counter.

## Better proposal
Same fix: add a daily beat entry that runs `call_command("clearsessions")`. Lazier option that removes the DB write completely: store the flag in a plain signed cookie (`response.set_signed_cookie`) instead of the session. That way an anonymous hit never creates a `django_session` row. Effort S.

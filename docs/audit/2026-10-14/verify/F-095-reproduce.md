# F-095 — Outbound README links get no rel=nofollow/noopener

**Lens:** reproduce
**Verdict:** REFUTED (as a security finding)
**Confidence:** medium-high
**Adjusted severity:** low (category: docs/simplification at most, not security)

## Reasoning

What holds:
- `bleach.clean(...)` at `django/main/views.py:371-377` uses no `linkify`/`LinkifyFilter`, so no `rel` is added to `<a>`.
- `target` is not in `ALLOWED_MARKDOWN_ATTRIBUTES["a"]` (`django/main/views.py:62-63`), and `_clean_attributes` (`views.py:77-87`) rejects it. No tabnabbing — finding agrees.

What does not hold:
- **Referrer leak: false.** `django.middleware.security.SecurityMiddleware` is enabled (`django/config/settings.py:58`) and `SECURE_REFERRER_POLICY` is not overridden anywhere (grep of `django/`, `tests/`). Django 5.1 (`pyproject.toml:10`) defaults it to `same-origin`, so cross-origin link clicks send no `Referer`. `infra/Caddyfile` sets no conflicting header.
- **noopener: irrelevant.** Without `target=_blank` there is no opener relationship to cut.
- **"Third-party links pass SEO weight": not a security issue.** Markdown comes from the site owner's own GitHub READMEs (`django/main/markdown_sync.py:44-60`, owner-repo parsing restricted to github.com), not user-generated content. Choosing whether to `nofollow` one's own outbound links is an SEO preference, not a vulnerability.

## Better proposal
None needed. If the owner wants `nofollow` for SEO reasons, add it when doing F-006 (nh3 `link_rel="nofollow"`); `noopener noreferrer` adds nothing given current policy and no `target`.

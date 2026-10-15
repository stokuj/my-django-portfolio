# F-034 — Every page is titled 'My Portfolio' (wrong block name)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning
- `django/main/templates/base.html:8` defines only `{% block title %}My Portfolio{% endblock %}`. No `page_name` block exists anywhere (grep over `django/` finds it only in the two child templates).
- `django/main/templates/pages/about.html:3` and `django/main/templates/projects/detail.html:4` override `{% block page_name %}`, which Django silently ignores, so both render `<title>My Portfolio</title>`.
- `errors/404.html:3` and `errors/500.html:3` already use `{% block title %}` correctly, so this is the established convention and the two pages are simply a typo/leftover, not a deliberate decision.
- `pages/home.html` and `projects/index.html` set no title (inherit default).
- No tests assert on `<title>`; renaming the block breaks nothing.

## Better proposal (smallest diff)
- Rename `page_name` -> `title` in `about.html:3` and `projects/detail.html:4` (2 lines).
- Add `{% block title %}Projects{% endblock %}` to `projects/index.html`.
- Home can keep the base default "My Portfolio" (it is the site landing page); adding one there is optional.
- Optional: base title `{% block title %}{% endblock %} | My Portfolio` pattern is not needed; keep it simple.

Effort: S.

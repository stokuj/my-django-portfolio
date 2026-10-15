# F-111 — Home and projects index have no title block; base default ignores site_name

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/main/templates/base.html:8`: `<title>{% block title %}My Portfolio{% endblock %}</title>` hardcodes the fallback.
- `django/main/context_processors.py:37` exposes `site_name` on every request; the navbar already uses it at `base.html:50` as `{{ site_name|default:"My Portfolio" }}`. Model default is `"My Portfolio"` (`django/main/models.py:172`), so the fix changes nothing until an admin edits `site_name`.
- `pages/home.html` and `projects/index.html` have no `{% block title %}` (grep finds title blocks only in `errors/404.html:3` and `errors/500.html:3`).
- No tests assert on `<title>`; nothing breaks. No docs or commits record the hardcoded title as deliberate.
- Worth doing, but it is the same 4-line change as F-034 and should ship with it. Severity lowered: the visible effect (all pages share one title) is already counted under F-034; the only extra here is the editable `site_name` not reaching `<title>` and a generic title on the projects list.

## Better proposal
Merge into the F-034 fix. In `base.html:8` reuse the navbar expression for consistency and an empty-value fallback:
`{% block title %}{{ site_name|default:"My Portfolio" }}{% endblock %}`.
Home keeps the default; `projects/index.html` adds `{% block title %}Projects | {{ site_name|default:"My Portfolio" }}{% endblock %}`; about/detail rename `page_name` to `title` per F-034.

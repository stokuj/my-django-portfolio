# F-111: Home and projects index have no title block; base default ignores site_name

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low

## Reasoning
- `django/main/templates/base.html:8`: `<title>{% block title %}My Portfolio{% endblock %}</title>` is hardcoded.
- `django/main/templates/base.html:50` already renders `{{ site_name|default:"My Portfolio" }}` in the navbar.
- `site_name` comes from `django/main/context_processors.py:37`, registered in `django/config/settings.py:81`, and the admin can edit it (`django/main/models.py:172`, default "My Portfolio").
- `django/main/templates/pages/home.html` (the finding says `home.html`; the real path is under `pages/`) and `django/main/templates/projects/index.html` define only `{% block content %}` and no `title` block.
- `pages/about.html:3` and `projects/detail.html:4` override `page_name`, a block that `base.html` does not define (F-034), so they also fall back to "My Portfolio".
- Impact: the title is wrong only when an admin changes `site_name` from its default. Until then it matches. This is SEO/UX polish with no functional break, so severity is lowered from medium to low.

## Better proposal
- base.html:8: `{% block title %}{{ site_name|default:"My Portfolio" }}{% endblock %}`. Keep the `|default` fallback for consistency with line 50, and because the 500 handler renders without context processors (500.html overrides the title anyway).
- projects/index.html: `{% block title %}Projects | {{ site_name|default:"My Portfolio" }}{% endblock %}`.
- home: the base default is enough; no block needed.
- Fix about/detail through F-034. Do it in one PR together with this one.

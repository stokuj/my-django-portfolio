# F-034 — Every page is titled 'My Portfolio' (wrong block name)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning
- `django/main/templates/base.html:8` defines only `{% block title %}My Portfolio{% endblock %}`. There is no `page_name` block anywhere in base.html (grep for `page_name` finds only the two child templates, and no Python code references it).
- `django/main/templates/pages/about.html:3` and `django/main/templates/projects/detail.html:4` override `{% block page_name %}`. Django ignores a child block that the parent does not define, so both pages render `<title>My Portfolio</title>`. The project title on the detail pages is lost.
- `django/main/templates/pages/home.html` and `django/main/templates/projects/index.html` define only `content` (line 3), so they fall back to the default title.
- Small overstatement: "every page" is not quite true. `errors/404.html:3` and `errors/500.html:3` correctly override `{% block title %}`. All normal content pages are affected.

## Better proposal
Rename `page_name` to `title` in about.html:3 and detail.html:4. Including the site name helps users tell tabs apart, e.g. `{% block title %}{{ project.title }} | My Portfolio{% endblock %}`. Add a `title` block to home.html and projects/index.html. A simple template test that asserts `<title>` on the detail page would catch a regression. Effort S.

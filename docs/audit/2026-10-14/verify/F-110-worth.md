# F-110 - No meta description on any page (worth lens)

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low (was medium)

## Reasoning
- `django/main/templates/base.html:5-9` head has only charset, viewport, theme-color, `<title>`, stylesheet. `grep -rn description django/main/templates` finds no `<meta name="description">` anywhere.
- Data is in context on every page: `profile_home_intro` / `profile_about_intro` (`django/main/context_processors.py:41-42`); `PortfolioProfile.home_intro` / `about_intro` are `CharField(max_length=255)` with non-empty defaults (`django/main/models.py:182-191`), so the base fallback is never empty. `Project.short_description` is `max_length=100` (`django/main/models.py:68`), good snippet length.
- Proposal is correct and additive: Django autoescape makes quotes safe inside `content="..."`. Nothing in git log or docs/ records a deliberate decision against it.
- Severity lowered: a missing meta description is not a bug; search engines fall back to page text. Nice-to-have for a personal portfolio.
- Path nit: the about template is `django/main/templates/pages/about.html`, not `about.html`. Detail page for projects is `projects/detail.html` (blog_detail view, `views.py:399-408`).

## Better proposal
Same as the finding, one block in base:
`<meta name="description" content="{% block meta_description %}{{ profile_home_intro }}{% endblock %}">`
plus overrides in `pages/about.html` (`{{ profile_about_intro }}`) and `projects/detail.html` (`{{ project.short_description }}`).
Related, likely higher SEO value at same cost: no page overrides `{% block title %}` except error pages (`errors/404.html:3`, `errors/500.html:3`), so every page is titled "My Portfolio" (`base.html:8`). Do both in one change.

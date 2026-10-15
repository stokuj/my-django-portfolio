# F-110: No meta description on any page (reproduce lens)

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low (original: medium)

## Reasoning
- `django/main/templates/base.html:4-12`: head has charset, viewport, theme-color, `<title>`, stylesheet and two scripts. No `<meta name="description">`.
- `grep -rn "<meta" django/main/templates/` matches only base.html:5-7. No template defines a description or a head-extension block.
- The data the proposal relies on exists:
  - `profile_home_intro` / `profile_about_intro` in `django/main/context_processors.py:41-42`, sourced from `PortfolioProfile.home_intro` / `about_intro` (`django/main/models.py:182-191`, CharField max 255 with non-empty defaults, so the fallback `PortfolioProfile()` still yields text).
  - `Project.short_description` at `django/main/models.py:68` (CharField max 100).
- `about.html:3` and `projects/detail.html:4` only override `page_name`/`content`/`sidebar`/`extra_scripts`, so adding a new `meta_description` block in base is additive and does not collide.

Severity: missing description is an SEO/share-preview gap, not a bug or security issue. Search engines fall back to page text. Low fits the scale ("nice to have") better than medium.

## Better proposal
Same as proposed, with autoescaping kept (default) and no `|safe`:
`<meta name="description" content="{% block meta_description %}{{ profile_home_intro }}{% endblock %}">` in base.html; override with `{{ profile_about_intro }}` in pages/about.html and `{{ project.short_description }}` in projects/detail.html.
Side note (not part of F-110): `{% block title %}` (base.html:8) is overridden only by errors/404.html:3 and errors/500.html:3, so all content pages share the title "My Portfolio"; worth fixing in the same change.

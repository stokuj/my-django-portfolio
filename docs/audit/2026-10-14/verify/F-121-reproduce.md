# F-121 — No Open Graph / Twitter card tags (reproduce)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `rg 'og:|twitter:'` over `django/` returns nothing. The only `<head>` is `django/main/templates/base.html:4-12`: charset, viewport, theme-color, `<title>`, CSS, two scripts. No `og:*`, `twitter:*` or even `<meta name="description">`.
- All pages extend `base.html` (projects/index, projects/detail, pages/home, pages/about, errors/404, errors/500), so no page emits share metadata.
- Scrapers fall back to `<title>`, but it is the static "My Portfolio" everywhere except the error pages (`errors/404.html:3`, `errors/500.html:3`). `projects/detail.html` does not override `{% block title %}`, so shared project links all show the same generic title.

## Inaccuracy in the proposal
- "reuse blocks" for og:description: no description block exists. Only `{% block title %}` is defined (`base.html:8`). A `{% block description %}` (and per-page title overrides) would have to be added first.

## Better proposal
1. In `base.html` add `{% block description %}` with a site default, plus `<meta name="description">`, `og:title` (`{% block title %}` cannot be rendered twice, so use a separate `{% block og_title %}` or pass via context), `og:description`, `og:type`, `og:url` (`request.build_absolute_uri`), `og:image`, `twitter:card`.
2. `og:image` must be absolute: `{{ request.scheme }}://{{ request.get_host }}{% static 'images/default_image.png' %}`, or `request.build_absolute_uri(project.thumbnail.url)` on detail.
3. Override title/description/image in `projects/detail.html` (`project.title`, project summary, `project.thumbnail`).
Effort: S.

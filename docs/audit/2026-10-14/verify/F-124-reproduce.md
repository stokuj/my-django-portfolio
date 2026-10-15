# F-124 reproduce: '#' fallback links: dead buttons, and a _blank that opens the same page

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/context_processors.py:31` sets `github_url = source.github_url or "#"`; `:44` sets `profile_email_href` to `"#"` when `email` is blank. `:32` does the same for `linkedin_url`, and `:34` makes `profile_github_base` `"#"`.
- `django/main/templates/components/hero/about_content.html:8` renders "Contact Me" with `href="{{ profile_email_href }}"`, so it becomes `href="#"` (does nothing). `:9` renders "GitHub" with `href="{{ profile_github_url }}" target="_blank"`, so it opens a new tab of the current page.
- `django/main/templates/base.html` has the same pattern: `:64` (GitHub, no `_blank`), `:128-130` (GitHub with `target="_blank"`), and `:159`, `:165`, `:177` (email `#` links; at `:177` the visible text is empty).
- Also reached by `django/main/templates/projects/components/project_footer.html:6`: `{{ profile_github_base }}/{{ repo_path }}` with `target="_blank"` becomes `#/<repo>`, which is another link that does nothing. The finding does not mention this one.
- When it happens: only when the active profile has `email`/`github_url` blank. The model defaults are placeholders (`django/main/models.py:203-204`). With no active profile, an unsaved `PortfolioProfile()` uses those defaults, so the fallback does not apply. An admin has to clear the field on purpose. There is no security impact, so the severity stays low.

## Better proposal
Return `""` instead of `"#"` from the context processor (lines 31, 32, 34, 44). Then wrap each link in `{% if profile_github_url %}` / `{% if profile_email %}`, including the guard for `project_footer.html:6`. Effort: S.

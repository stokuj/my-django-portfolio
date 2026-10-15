# gap-secondary-templates

Scope: errors/404.html, errors/500.html, components/hero/*_content.html, components/timeline_project_item.html, projects/components/{blog_sidebar_cards,blog_projects_sidebar,project_footer}.html, components/icons/*.html at HEAD (dev). This pass skips F-080, F-083, F-086 and F-094.

Verified OK (no finding):
- None of these templates uses `|safe` or `autoescape off`.
- Every `target="_blank"` in scope has `rel="noopener noreferrer"`.
- No N+1 queries:
  - `project.tags.all` (timeline_project_item.html:6) is prefetched (views.py:102).
  - The sidebar reads only scalar fields.
  - `all_projects` is one QuerySet included twice (detail.html:27,40), and its result cache is reused.
- Every context variable is supplied, either by the view (views.py:408-418) or by the context processors.
- Both icon SVGs are `aria-hidden="true"`, and their parent links have `aria-label` (base.html:66,75,131,141).
- No dead includes: every file in scope is included.

Already covered elsewhere, so not repeated here:
- 500.html extends base.html and hits the DB through the context processors: F-040.
- project_footer.html:6 builds the link from profile_github_base/repo_path: F-069.
- hero_section_class and hero_inner_class are never passed: F-094.
- page_name block: F-034.

## 1. Duplicate and ambiguous "Learn More" link in the timeline item
- Severity: low | Category: frontend | Effort: S
- File: django/main/templates/components/timeline_project_item.html:13-17
- Problem: a project with `blog=False` and a `github_url` gets two buttons that point to the same URL: "Learn More" (13-14) and "GitHub" (16-17). The label "Learn More" also behaves in two ways. It opens in the same tab for a blog post and in a new tab for GitHub. The text is generic and repeats once per project.
- Proposal: remove the `{% elif project.github_url %}` branch (13-14), because the GitHub button already covers that case. Optionally add `aria-label="Learn more about {{ project.title }}"`.
- Risk: none. Non-blog projects lose a redundant button.

## 2. `<time>` without a machine-readable `datetime`
- Severity: low | Category: frontend | Effort: S
- File: django/main/templates/components/timeline_project_item.html:2
- Problem: `<time>{{ project.date|date:"F Y" }}</time>` has no `datetime` attribute. Text such as "May 2022" is not a valid time string, so the element carries no machine-readable value.
- Proposal: `<time datetime="{{ project.date|date:'Y-m' }}">`.
- Risk: none.

## 3. Current project in the sidebar is marked only by CSS
- Severity: low | Category: frontend | Effort: S
- File: django/main/templates/projects/components/blog_projects_sidebar.html:8
- Problem: the project currently open is marked only with the `active` class. Screen readers get no "current page" cue. F-080 covers base.html nav only.
- Proposal: add `{% if sidebar_project.id == project.id %}aria-current="page"{% endif %}` next to the class.
- Risk: none.

## 4. Non-list JSON in tech_stack/tools_libraries renders one badge per character
- Severity: low | Category: bug | Effort: S
- File: django/main/templates/projects/components/blog_sidebar_cards.html:6,19 (fields at django/main/models.py:66-67)
- Problem: `tech_stack` and `tools_libraries` are `JSONField(default=list)` with no validator. They are editable in the admin (admin.py:20-21). If an admin enters `"Django, DRF"` (valid JSON, a string), the value is truthy, and `{% for item in project.tech_stack %}` iterates over its characters. The result is one badge per character, rendered twice (mobile and desktop sidebar).
- Proposal: add a small model validator that rejects anything other than a list of strings, and put it on both fields.
- Risk: existing rows with bad data fail on the next admin save until they are fixed. This is intended.

## 5. "#" fallback links: dead buttons, and a `_blank` that opens the same page
- Severity: low | Category: frontend | Effort: S
- File: django/main/templates/components/hero/about_content.html:8-9 (fallback at django/main/context_processors.py:31,44)
- Problem: the context processor uses `"#"` as the fallback for a blank profile `github_url` or `email`.
  - "Contact Me" then goes nowhere.
  - "GitHub" has `target="_blank"`, so it opens a second copy of the About page in a new tab.
  - The same `#` links also appear in base.html.
  - This happens only when the active profile has these fields blank; the model defaults are placeholders, not empty.
- Proposal: in the template, render each button only when its value is set (`{% if profile_email %}`, `{% if profile_github_url != "#" %}`). Or return `""` from the context processor and guard on truthiness.
- Risk: none.

## 6. Inconsistent `target` on the shared social icon links
- Severity: low | Category: frontend | Effort: S
- File: django/main/templates/base.html:63-78 (header) vs base.html:127-141 (footer)
- Problem: the header and footer GitHub/LinkedIn icon links point to the same URLs. The header links open in the same tab, with no `target` or `rel`. The footer links use `target="_blank" rel="noopener noreferrer"`. F-086 noted the difference only as a reason to skip an include and did not flag the UX inconsistency.
- Proposal: choose one behaviour. Simplest: add `target="_blank" rel="noopener noreferrer"` to the two header links (63, 72). Or remove `target="_blank"` from the footer.
- Risk: none.

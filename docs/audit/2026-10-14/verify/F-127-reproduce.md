# F-127: Current project in the sidebar is marked only by CSS (reproduce)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/templates/projects/components/blog_projects_sidebar.html:8`: the link to the current project gets only `class="... active"` when `sidebar_project.id == project.id`. The repo's templates contain no `aria-current` anywhere.
- The view at `django/main/views.py:406-413` passes `project` and `all_projects`, so the comparison runs on the blog detail page.
- The partial is included twice in `django/main/templates/projects/detail.html` (lines 27 and 40). Both copies have the same gap. Only one is visible at a time (`2xl:hidden` / `hidden 2xl:block`), and `display:none` hides the other from assistive tech too, so the duplicate include is fine.
- Screen readers get no cue for the current page, which is an accessibility basic. Low severity is right.

## Better proposal
Same as proposed, on line 8 only (the github_url and plain-span branches can never be the current blog page):
`{% if sidebar_project.id == project.id %}aria-current="page"{% endif %}`
Optionally, merge both conditions into one `{% if %}` block that outputs the class and the attribute together.

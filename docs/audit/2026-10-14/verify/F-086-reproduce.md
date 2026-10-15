# F-086 - Template duplication (img blocks, status badge, social icons)

- Lens: reproduce
- Verdict: CONFIRMED (partially; the status-badge part is wrong as stated)
- Confidence: medium
- Adjusted severity: low

## Reasoning

1. **img blocks - confirmed.** `django/main/templates/projects/components/project_card.html:10-18` and `:20-28` are identical except `src` and `alt`.

2. **Status badge - mostly wrong.**
   - The project status chain (`project_card.html:35-41`) occurs only once; grep for `status ==` across templates finds no other project-status chain.
   - `about.html:143-151` and `:207-215` handle a different domain: task status (`success`/`partial_success`/`failure`), not project status (`planned`/`ongoing`/`finished`, `models.py:80-90`). One include cannot serve both without separate mappings.
   - `get_status_display` does not help:
     - `scheduled_jobs` entries are plain dicts (`views.py:298-310`), so they have no `get_status_display`.
     - The method returns only the label, not the badge CSS class. The CSS class is what the if/elif chain actually chooses.
     - It would change the visible text (`partial_success` -> `Partial success`).
     - The two about.html chains also have different fallbacks (`never` vs `unknown`).
   - What is actually duplicated: the two about.html task-status chains share the same 3-way mapping.

3. **Social icons - confirmed but low value.** The links appear twice in `base.html`, at `:62-78` (navbar) and `:123-141` (footer), and both use the shared icon includes. The two variants differ in classes (`hidden sm:inline-flex` vs `hover:bg-base-300`) and in `target="_blank" rel="noopener noreferrer"` (footer only). An include would need parameters to cover those differences, which saves very little.

## Better proposal

- One `<img>` with `src="{% if project.thumbnail %}{{ project.thumbnail.url }}{% else %}{% static 'images/default_image.png' %}{% endif %}"`, and the same pattern for `alt`. Effort S.
- Optional: a `components/task_status_badge.html` include with `status` and `fallback` parameters for the two about.html chains. Leave the project card as it is.
- Skip the social-icons include: the variants differ, and each already reuses the icon includes.

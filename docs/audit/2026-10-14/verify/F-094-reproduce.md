# F-094 — Small dead bits in views and templates

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low (simplification)

## Reasoning
- `django/main/views.py:134` sets `"heatmap_component_visible": True` unconditionally; it is the only producer (grep over `django/`, `tests/`). It is read only by `pages/about.html:47` and `:257`, so both `{% if %}` guards are always true.
- `django/main/views.py:414` passes `blog_markdown_content`; no template or test reads it. Only `blog_markdown_html` is used.
- `django/main/views.py:340-354` `_load_project_markdown` does `open("rb")` / `read().decode("utf-8")` / `finally: close()` wrapped in a try for `OSError`.
- Small inaccuracy: the BOM strip (`lstrip("﻿")`) is at `views.py:361`, inside `_render_markdown_to_html`, not `_load_project_markdown`. Its only input comes from `_load_project_markdown` (`views.py:402-403`), so moving the BOM handling into the decode still works. `markdown_sync.py:129` already uses `decode("utf-8-sig")`, so that is the existing pattern.
- `components/hero_section.html:2-3` read `hero_section_class` and `hero_inner_class`. None of the 5 includes pass them (`home.html:6`, `about.html:7`, `projects/index.html:6`, `errors/404.html:7`, `errors/500.html:7`). Both render as empty strings.

## Better proposal
- Delete the `heatmap_component_visible` key and the two `{% if heatmap_component_visible %}` / `{% endif %}` pairs in `about.html`. The context key cannot go on its own.
- Delete the `blog_markdown_content` key.
- In `_load_project_markdown`: `with project.markdown_file.open("rb") as f: return f.read().decode("utf-8-sig")`, catching `(OSError, UnicodeDecodeError)`. Then drop `views.py:361`. Note: `lstrip` removes repeated BOMs and `utf-8-sig` removes only one. This difference does not matter in practice.
- Remove `{{ hero_section_class|default:'' }}` and `{{ hero_inner_class|default:'' }}`.
- Risk: none functional. Effort: S.

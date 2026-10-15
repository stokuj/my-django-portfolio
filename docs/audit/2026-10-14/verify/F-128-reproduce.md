# F-128 reproduce: Non-list JSON in tech_stack/tools_libraries renders one badge per character

Verdict: CONFIRMED
Confidence: high
Adjusted severity: low

## Reasoning
- `django/main/models.py:66-67`: `tech_stack` / `tools_libraries` are `JSONField(default=list, blank=True)`, no validators.
- `django/main/admin.py:12-23`: `ProjectAdmin` defines no `fields`/`exclude`, so both fields are editable in the change form (the cited lines 20-21 are `list_display`, but editability holds via the default form).
- `django/main/templates/projects/components/blog_sidebar_cards.html:6,19`: `{% for item in project.tech_stack %}` / `tools_libraries` iterate the raw value.
- The component is included twice in `django/main/templates/projects/detail.html:28,45` (mobile and desktop), so both render.
- Reproduced (Django 5.1.15): `forms.JSONField().clean('"Django, DRF"')` returns the str `'Django, DRF'`; the for loop over it renders `[D][j][a][n][g][o][,][ ][D][R][F]`.
- Caveat: input must be a quoted JSON string; unquoted `Django, DRF` is invalid JSON and the admin form rejects it. A dict would render its keys; a bare number makes the template raise a TypeError (500 on the detail page) - slightly worse than described.
- Admin-only input (trusted user), so it's a data-entry footgun, not a security issue. Low is right.

## Better proposal
Same fix, minimal: one module-level `validate_str_list(value)` in models.py raising `ValidationError` unless `isinstance(value, list) and all(isinstance(i, str) for i in value)`, added as `validators=[...]` to both fields. It needs a migration (validators are recorded in migrations; no schema change). Add one test in `main/tests/test_models.py` calling `full_clean()` with a str value.

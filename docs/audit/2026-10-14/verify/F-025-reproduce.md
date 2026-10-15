# F-025 (reproduce lens): Admin 500 when adding a tag that differs only in case

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/main/models.py:44`: `name = CharField(max_length=50, unique=True)`.
- `django/main/models.py:46-48`: `save()` uppercases `name` only at save time.
- `django/main/admin.py:115`: `admin.site.register(Tag)` uses the default ModelAdmin and ModelForm.
- `ModelForm._post_clean` runs `instance.full_clean()` and then `validate_unique()` on the raw value "python". The exact lookup is case-sensitive on both SQLite and PostgreSQL, so it does not match the stored "PYTHON". `save()` then writes "PYTHON" and the DB unique constraint raises `IntegrityError`, which the admin returns as a 500.
- Reproduced with a probe kept outside the repo (/tmp/f025/probe.py, in-memory SQLite, the real `admin.site._registry[Tag].get_form()`). Output: `form valid: True` followed by `IntegrityError UNIQUE constraint failed: main_tag.name`.
- The attack path is only reachable by staff in the admin. No other code writes Tag in non-test code (the only other use is the read at `views.py:328`). The DB constraint still blocks the duplicate, so no data is lost. That is why I lowered the severity to low.

## Proposal check
- I monkeypatched `Tag.clean = lambda self: setattr(self, 'name', self.name.upper())` into the probe. With it the form is invalid with `{'name': ['Tag with this Name already exists.']}`, so the proposed fix works with no migration. Keep `save()` for paths that do not use a form.
- No better proposal. A `UniqueConstraint(Upper("name"))` would need a migration and would still need `clean()` to give a friendly error.

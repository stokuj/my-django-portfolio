# F-025 (worth) - Admin 500 when adding a tag that differs only in case

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/main/models.py:45` `name` is `unique=True`; `django/main/models.py:47-49` `save()` uppercases after form validation.
- ModelForm `_post_clean` runs `instance.full_clean()` (which calls `Model.clean()`) before `form.validate_unique()`, so normalizing in `clean()` makes the unique check see the uppercased value.
- Probe (in-memory sqlite, Django 5.1.15, nothing written to the repo): with `Tag(name="PYTHON")` already present, a `ModelForm` given `"python"` passes `is_valid()` and `save()` raises `IntegrityError: UNIQUE constraint failed: main_tag.name`. After adding `clean()` to uppercase `name`, `is_valid()` is False with "Tag with this Name already exists.", and a new tag `"rust"` still saves as `RUST`.
- The only write path is the stock admin (`django/main/admin.py:115`). No code calls `Tag.objects.create`/`get_or_create`, so keeping `save()` costs nothing and still covers shell use. Nothing in the git history suggests the uppercasing was meant to fail this way.
- Severity lowered: the only person affected is the single admin (the owner), they get a 500 page, and no data is lost. The fix is still worth making because it's small.

## Better proposal
None needed. The proposal is the smallest correct diff: a 2-line `clean()`, no migration. An alternative is `UniqueConstraint(Upper("name"))`, which Django 5.1 validates in forms, but it needs a migration and is more code. Not worth it here.

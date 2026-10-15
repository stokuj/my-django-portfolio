# F-118 - TaskExecutionStatus/Log admins allow add and delete of system rows

**Lens:** reproduce
**Verdict:** CONFIRMED (mechanics); security framing overstated
**Confidence:** high
**Adjusted severity:** low (category: simplification / admin hygiene, not security)

## Reasoning

- `django/main/admin.py:63-86` and `:89-112`: both admins mark every model field readonly and override none of `has_add_permission`, `has_change_permission`, `has_delete_permission`. Add, change and delete views are therefore exposed to anyone with the default model perms (superuser in practice).
- Add on `TaskExecutionStatus`: readonly fields are excluded from the ModelForm, so the instance saves with defaults (`task_name=""`). `validate_unique` skips excluded fields, so a second add raises an `IntegrityError` on `unique=True` (`django/main/models.py:130`), which shows up as a 500 rather than a form error.
- Change view: the Save button re-saves an unchanged row. That is a no-op, not a bug.
- Delete impact is limited:
  - Status rows heal themselves. Tasks use `get_or_create` (`django/main/tasks.py:31`, `:114`, `:206`), so a deleted snapshot comes back on the next beat run.
  - The about page reads statuses through `filter(task_name__in=...)` (`django/main/views.py:268`), so a blank row is never shown.
  - Deleting `TaskExecutionLog` rows does lose history permanently, but only the site owner can do it.
- Why it is not security: reaching these views takes staff status plus model perms. On this single-owner portfolio that means the owner. No privilege boundary is crossed; the cost is a clumsy admin UI and a possible self-inflicted 500.

## Better proposal

Make both admins view-only with one override each, or a shared mixin, or just copy the methods:

```python
def has_add_permission(self, request): return False
def has_change_permission(self, request, obj=None): return False
```

Keep delete. Pruning old log rows is a legitimate owner action. Effort S.

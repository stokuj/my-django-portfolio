# F-117 (reproduce): ProjectAdmin and TaskExecutionLogAdmin list views are hard to use

- Verdict: CONFIRMED (partially). The ordering claim is REFUTED.
- Confidence: high
- Adjusted severity: low

## Reasoning
Confirmed at HEAD:
- `django/main/admin.py:14-22`: ProjectAdmin `list_display` includes `markdown_file`, `tech_stack`, `tools_libraries`. The two JSONFields (`models.py:66-67`) show as Python list reprs in the changelist.
- ProjectAdmin has only `search_fields` (`admin.py:23`). It has no `list_filter`, `filter_horizontal` or `ordering`. `tags` is an M2M (`models.py:79`), so the change form uses the default multi-select widget.
- `admin.py:89-112`: TaskExecutionLogAdmin has no `list_filter` and no `date_hierarchy`.
- `admin.py:115`: `Tag` is registered with no ModelAdmin, so it has no search.

Refuted: "the oldest runs are listed first". It is true that TaskExecutionLog has no `Meta.ordering` (`models.py:146-166`) and its admin sets no `ordering`. But Django admin's `ChangeList._get_deterministic_ordering` (`django/contrib/admin/views/main.py:432-495` in the installed Django) appends `"-pk"` when no ordering gives a total order. The changelist is therefore newest first. `created_at` is `auto_now_add` (`models.py:163`), so `-pk` already matches `-created_at`. For the same reason, Project already lists newest first by pk.

This is a usability nit with no bug or security impact.

## Better proposal
- ProjectAdmin: drop `markdown_file`, `tech_stack` and `tools_libraries` from `list_display`. Add `date`, plus `list_filter = ("status", "blog", "tags")` and `filter_horizontal = ("tags",)`. Add `ordering = ("-date",)` only if listing by project date is wanted rather than by insertion order.
- TaskExecutionLogAdmin: `list_filter = ("task_name", "last_status")` and `date_hierarchy = "created_at"`. No ordering change is needed.
- Tag: optional `search_fields = ("name",)`.
- Effort: S.

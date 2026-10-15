# F-091 - Home timeline duplicates Project.STATUS_CHOICES

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low

## Reasoning
- `django/main/views.py:103-108` hardcodes `status_labels` (`planned`/`ongoing`/`finished` -> labels) and `status_order`, a verbatim copy of `Project.STATUS_CHOICES` at `django/main/models.py:81-85` (same keys, same labels, same order).
- Used only in `home()` (`views.py:110`, `118`, `122`); no other callers. Template `pages/home.html:15` consumes only `timeline_sections`; `tests/test_views.py:56` only checks the key exists.
- Real drift risk: adding a status to the model would silently drop those projects from the home page (`views.py:112` filters by `projects_by_status`). Not a current bug, just duplication.

## Better proposal
Drop both locals and iterate the model choices:
```python
projects_by_status = {status: [] for status, _ in Project.STATUS_CHOICES}
...
timeline_sections = [
    {"status": s, "title": label, "checked": s == "finished", "projects": projects_by_status[s]}
    for s, label in Project.STATUS_CHOICES
]
```
Effort S, no behavior change.

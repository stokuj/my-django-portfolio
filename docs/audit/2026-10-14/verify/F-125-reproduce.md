# F-125 — `<time>` without a machine-readable datetime (reproduce)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/templates/components/timeline_project_item.html:2` renders `<time ...>{{ project.date|date:"F Y" }}</time>` with no `datetime` attribute.
- `Project.date` is a `DateField` (`django/main/models.py:69`), so the output is e.g. `May 2022`. Per the HTML spec, a `<time>` with no `datetime` attribute must have a valid date/time string as its text content. `May 2022` is not one (the valid month string is `2022-05`), so the element carries no machine-readable value.
- The template is reachable: it is included from `django/main/templates/components/timeline_section.html:7`.
- Every other `<time>` in the codebase sets `datetime` (`django/main/templates/pages/about.html:159,166,221,226,234`), so this one is the only exception.
- The impact is cosmetic or semantic only (validators, crawlers). Nothing breaks for users.

## Better proposal
None. The proposed fix `<time datetime="{{ project.date|date:'Y-m' }}">` is correct and minimal. `Y-m` gives a valid month string that matches the "F Y" display precision.

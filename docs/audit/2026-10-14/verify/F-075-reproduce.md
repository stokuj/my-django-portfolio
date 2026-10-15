# F-075 - Tag filter state shown only by color (no aria-pressed)

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low

## Reasoning
- `django/main/static/js/projects-filters.js:76-82`: the click handler only swaps `btn-primary`/`btn-outline` classes; no ARIA attribute is set anywhere in the file.
- `django/main/templates/projects/index.html:32-36`: `#tagFilter` buttons have no `aria-pressed`, no `role="group"`/`aria-label`; initial "All" state is also class-only.
- Partial mitigation: `index.html:71` has an `aria-live` region announcing "N projects shown", but it does not say which tag is active, so the pressed state remains invisible to assistive tech.

## Better proposal
Set `aria-pressed="true"` on the "All Projects" button and `aria-pressed="false"` on tag buttons in the template, then in the loop at `projects-filters.js:76`: `btn.setAttribute("aria-pressed", btn === button)` alongside the class swap. Optionally `role="group" aria-label="Filter by tag"` on `#tagFilter`. Effort S.

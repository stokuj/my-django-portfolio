# F-036: Server-rendered project grid hidden behind a fake skeleton until JS runs

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/main/templates/projects/index.html:40-60`: `#projectGridSkeleton` renders 6 placeholder cards and is visible by default.
- `django/main/templates/projects/index.html:62-66`: `#projectGrid` holds the real server-rendered cards and ships with class `hidden`.
- `django/main/static/js/projects-filters.js:89-90`: the only place that unhides the grid and hides the skeleton. It runs on DOMContentLoaded and only if the guard at `:11` passes.
- No `<noscript>` fallback anywhere in templates (grep). Script is loaded at `index.html:75` with `defer`.
- So with JS disabled, blocked, or failing before line 89 (e.g. the early return at `:11`, or an exception), users see only skeleton cards and never the projects. Reproduces as described.
- The skeleton adds nothing: the data is already in the HTML, so there is nothing to load.

## Overstatement
- "crawlers see only skeleton cards": overstated. Non-rendering crawlers read the raw HTML, which already has the full card markup (display:none does not remove it). Rendering crawlers (Googlebot) run the JS. SEO impact is small.
- The real impact is only no-JS or broken-JS users, which is rare. Hence low, not medium.

## Proposal
The finding's proposal is correct: delete `index.html:40-60`, drop `hidden` from `index.html:62`, delete `projects-filters.js:8`, `:89-90`, and remove `|| !projectGridSkeleton` from the guard at `:11` (the proposal does not mention it; leaving it would make the script return early and break all filtering). Keep `applyFilters()` at `:88` (it sets the sr-only results status).

# F-085 (reproduce): Heatmap is not accessible

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/templates/pages/about.html:398-421`: each day is a plain `document.createElement("div")` with `aria-label` (and `title`) set. `normalizeDays` (`:322-328`) pads every week to 7 days, so ~53 weeks x 7 = ~371 generic divs. ARIA 1.2 prohibits `aria-label` on role `generic`, so screen readers mostly ignore it.
- `:82` `#heatmap-minimal-grid` and the week column wrappers (`:396-397`) have no role or accessible name. No summary of the chart is exposed.
- `:53` `#heatmap-minimal-status` has no `aria-live`/`role="status"`. `:57` `#heatmap-minimal-error` (DaisyUI `alert` class only) has no `role="alert"` either, so the error from `showError` (`:301-305`) is not announced.
- Caveat on the proposal: on success and on error the status element is hidden (`:302`, `:454`). An `aria-live` on it would at most announce the disabled-token text (`:310`). It does not announce the result. The error box is the region that needs announcing.
- Mitigation: the visible stat cards (`:62-73`: username, 12-month total, 30-day total) already give a text summary of the data. So the impact is low.

## Better proposal
- Grid (`:82`): `role="img"` plus an `aria-label` set in `renderGrid`, e.g. "GitHub contributions heatmap, N contributions in the last 12 months". The month labels row (`:79`) gets `aria-hidden="true"`.
- Cells (`:421`): drop `setAttribute("aria-label", ...)` and keep `title` for mouse users. Children of `role="img"` are presentational anyway.
- Error box (`:57`): add `role="alert"`. Status (`:53`): `role="status"` is optional, only for the loading and disabled text.
- Effort: S.

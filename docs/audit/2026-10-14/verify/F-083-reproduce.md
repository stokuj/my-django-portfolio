# F-083 — Timeline accordion uses unlabelled radio inputs

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/templates/components/timeline_section.html:2` — `<input type="radio" name="timeline-accordion" ...>` has no `id`/`<label for>`, no `aria-label`/`aria-labelledby`, and is not wrapped in a `<label>`.
- `timeline_section.html:3` — the title is a plain `<div class="collapse-title">`, not associated with the input, so the radio has no accessible name.
- Reachable: included for every section on the home page, `django/main/templates/pages/home.html:15-16`.
- This is daisyUI's documented radio-accordion pattern, so it renders and works visually; the gap is accessibility only. Low severity is right.
- daisyUI `^5.0.28` (`package.json:9`) supports `<details class="collapse">` + `<summary class="collapse-title">`, and the native `name` attribute on `<details>` gives exclusive-accordion behaviour, so the proposal is valid.

## Better proposal
Proposal stands (native `<details name="timeline-accordion" {% if section.checked %}open{% endif %}>` + `<summary>`: built-in name, keyboard support and expanded state).
Smaller alternative if the markup should stay: add `aria-label="{{ section.title }}"` to the radio at line 2. Effort S either way.

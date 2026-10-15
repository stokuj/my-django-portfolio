# F-074 - Unnecessary debounce and JS clear button in projects filter

- Lens: reproduce
- Verdict: CONFIRMED (debounce part); clear-button part is optional / taste
- Confidence: high
- Adjusted severity: low (unchanged)

## Reasoning
- `django/main/static/js/projects-filters.js:16-34` defines a 150 ms debounce timer plus two wrappers: `applyFiltersDebounced` (18-26) and `applyFiltersImmediate` (28-34). Only the `input` listener uses the debounced one (65). The clear button (69) and tag buttons (84) use the immediate one, which only exists to cancel the pending timer.
- `applyFilters` (36-63) does a substring check on two `data-*` attributes per card and sets `style.display`. That is O(n) with no network or layout reads.
- `django/main/views.py:323-337` renders every project with no pagination (`Project.objects.order_by(...)`), so n is the size of a personal portfolio, a few dozen at most. Running the filter on each keystroke costs almost nothing, so the debounce does not help.
- Correction to the finding's wording: the input is `type="text"` (`django/main/templates/projects/index.html:14`), not `type="search"`. The page does not use a native clear control today. The custom `#clearButton` (index.html:19-28) is wired at JS 66-70 and toggled at JS 38. It is also part of the early-return guard at JS 11, so removing it means editing the guard, line 38 and the listener.
- No tests reference the debounce or the clear button (grep of `django/main/tests`, `tests/`).

## Better proposal
1. Remove `searchDebounceTimer`, `applyFiltersDebounced` and `applyFiltersImmediate`. Use `searchInput.addEventListener("input", applyFilters)` and call `applyFilters()` directly at 69 and 84. This saves about 19 lines and carries no behaviour risk. Effort S.
2. Switching to `type="search"` and dropping `#clearButton` is optional. Firefox shows no clear "x", and the button styling is deliberate UI. Treat it as a design choice, not a defect. If you do it, also remove `clearButton` from the guard (11) and the toggle (38).

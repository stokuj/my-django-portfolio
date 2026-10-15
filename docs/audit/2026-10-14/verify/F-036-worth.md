# F-036 (worth lens): Server-rendered project grid hidden behind a fake skeleton until JS runs

**Verdict:** CONFIRMED (proposal is incomplete as written)
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `django/main/templates/projects/index.html:40-60` renders 6 placeholder skeleton cards. The real cards are already server-rendered in `#projectGrid` at :62-66, which ships with the `hidden` class (:62).
- The grid becomes visible only via `django/main/static/js/projects-filters.js:89-90`. Without JS, or if the script fails or 404s, visitors see skeletons forever. Crawlers and link previews that don't run JS get the content as `display:none`.
- Nothing loads asynchronously, so the skeleton has nothing to wait for. On first load, `applyFilters()` (:88) uses `activeTag="all"` and an empty search, so it hides nothing. The skeleton only delays content that is already in the DOM.
- No deliberate decision is recorded: commit `4cee56f` ("Implemented loading skeleton state on") gives no rationale, and nothing in docs/ mentions it. No tests reference `projectGrid` or `projectGridSkeleton` (`django/main/tests`).

## Correction to the proposal
Deleting only "the two toggle lines" (:89-90) would break filtering. Line 11 has an early-return guard, `|| !projectGridSkeleton`. Once the skeleton element is gone, that guard returns early, and search and tag filters stop working. All of these must be removed together:
- `index.html:40-60` (skeleton block) and `hidden` on :62
- `projects-filters.js:8` (const), `!projectGridSkeleton` in the :11 guard, and :89-90. After that, `projectGrid` is used only in the guard, so drop it from :7 and :11 as well.

## Better proposal
Same delete, done completely: about 25 lines removed, nothing added. Effort S. Risk: if the browser restores a search value on back-navigation, the unfiltered grid may flash briefly before `applyFilters()` runs. That is acceptable.

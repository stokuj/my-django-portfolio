# F-028: Dark mode ignores OS preference, flashes light, carries legacy migration code (reproduce lens)

**Verdict:** CONFIRMED, but the proposal is incomplete as written
**Confidence:** high
**Adjusted severity:** low (cosmetic, no data or security impact)

## Reasoning
- The script is deferred (`django/main/templates/base.html:10`) and its body runs on `DOMContentLoaded` (`django/main/static/js/theme-toggle.js:1`). `<html>` is server-rendered with `data-theme="fantasy3"` (`base.html:3`). A user who saved `dim2` can see light paint before the script runs, so the flash is real.
- Both themes set `prefersdark: false` (`django/main/static/src/css/input.css:108`, `:144`). With no saved value, the script writes `fantasy3` (`theme-toggle.js:32-33`). Nothing in templates/js/css checks `prefers-color-scheme` (grep finds no hits). OS preference is never used.
- No try/catch around `localStorage` (`theme-toggle.js:8,29,33,44`). If storage throws, the handler aborts before the toggle listener is attached. Impact is small: the page still renders `fantasy3` from `base.html:3`, and daisyUI's `.theme-controller` checkbox (`base.html:84`) still switches theme through CSS for the session. Only persistence is lost.
- `legacyThemeMap` (`theme-toggle.js:7,9,28-30`) only matters to visitors who still have `fantasy2` saved from before commit 2946e96. It is dead weight in practice.

## Proposal issue
`prefersdark: true` alone does nothing. daisyUI 5 applies a prefersdark theme only to `:root:not([data-theme])`, and `<html>` always has `data-theme` (hardcoded at `base.html:3` and set again by JS). The fix has to happen in JS.

## Better proposal
1. Replace the deferred load with a tiny inline `<head>` script:
   `try{var t=localStorage.getItem('theme')}catch(e){} document.documentElement.dataset.theme = t==='dim2'||t==='fantasy3' ? t : (matchMedia('(prefers-color-scheme: dark)').matches ? 'dim2' : 'fantasy3');`
2. Keep the deferred script only to sync the checkbox, update the theme-color meta and handle `change`. Write to storage only on `change`, wrapped in try/catch.
3. Delete `legacyThemeMap`. Leave the `prefersdark` flags alone, since they are irrelevant once JS sets `data-theme`.

Effort: S.

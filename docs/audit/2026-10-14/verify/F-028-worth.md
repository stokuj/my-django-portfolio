# F-028 (worth): Dark mode ignores OS preference, flashes light, carries legacy migration code

**Verdict:** CONFIRMED in part (flash is real); the proposed fix is partly wrong. Adjusted severity: **low**.
**Confidence:** medium

## Reasoning
- **Flash: real, but narrow.** `base.html:3` hardcodes `data-theme="fantasy3"`, and `theme-toggle.js` is loaded with `defer` (`base.html:10`) and runs on DOMContentLoaded (`theme-toggle.js:1`). Only visitors who saved `dim2` see a light frame. That is cosmetic, so low rather than medium.
- **`prefersdark:true` would do nothing.** As I understand daisyUI, `prefersdark` only applies under `prefers-color-scheme: dark` when the root has no `data-theme`. `base.html:3` always sets one, and the JS always sets one too (`theme-toggle.js:23,32`). So the proposed CSS change has no effect.
- **OS preference looks like a design choice, not a bug.** Light is the explicit default in three places: `base.html:3`, `defaultTheme` (`theme-toggle.js:5`) and `theme-color #fef8ea` (`base.html:7`). Following the OS would be a feature request. The finding's own "risk" line admits it changes what users see.
- **Missing try/catch: low.** If storage throws, the script stops. The page still renders in light because of `base.html:3`; only the toggle stops working.
- **legacyThemeMap:** added on purpose in `2946e96` ("Fix issue with old theme", Feb 2026). It is 3 lines (`theme-toggle.js:7,9,28-30`). After 8 months most returning visitors have already been migrated, so deleting it is optional, harmless cleanup.

## Better proposal (smallest diff)
1. Add an inline `<head>` script before the stylesheet:
   `<script>try{var t=localStorage.getItem("theme");if(t==="dim2")document.documentElement.dataset.theme=t}catch(e){}</script>`
   This removes the flash, with no CSS change.
2. Wrap the `localStorage` calls in `theme-toggle.js` in try/catch. Optionally delete `legacyThemeMap`.
3. Skip OS-preference support unless the owner wants it. If they do, add `matchMedia('(prefers-color-scheme: dark)')` to the same inline script and stop writing the default at `theme-toggle.js:33`. Do not rely on `prefersdark`.

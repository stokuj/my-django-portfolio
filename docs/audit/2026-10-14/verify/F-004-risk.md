# F-004 (risk lens): Mobile menu likely never opens in Safari/iOS; JS reimplements native popover

**Verdict:** CONFIRMED (the bug). The proposed fix carries more risk than the finding says.
**Confidence:** medium-high. Checked against the code and the installed daisyUI 5.0.28 CSS. Not run in a browser.
**Adjusted severity:** high (unchanged).

## Reasoning
- `base.html:25-47`: a `.dropdown` wrapper holds a `<button>` and `ul.dropdown-content.hidden`. `package.json:9` declares `daisyui ^5.0.28`, and 5.0.28 is the version installed.
- Installed CSS, `node_modules/daisyui/components/dropdown.css`: `.dropdown:not(details,.dropdown-open,.dropdown-hover:hover,:focus-within) .dropdown-content{display:none}`. The menu can only show when the wrapper has focus within it or has `.dropdown-open`.
- `mobile-menu.js:9-12` toggles only `hidden` and `aria-expanded`. It never adds `.dropdown-open`. WebKit does not focus a `<button>` on click (daisyUI's docs give this as the reason they use `div tabindex=0`). So on Safari/iOS the menu stays `display:none`.
- Impact: below `md` this menu is the only site navigation, because the desktop links at `base.html:54` are `hidden md:flex`. High severity is justified.
- The secondary claims hold. When focus leaves the dropdown (on Chromium), daisyUI hides the menu but `aria-expanded` stays `true`, so the next tap takes two presses. The Escape handler at `mobile-menu.js:27-32` calls `button.focus()` without checking whether the menu is open.
- No tests cover this. Grepping the tests for `mobile-menu` or `dropdown` finds nothing.

## Risks of the proposed fix (popover + popovertarget)
- The fix is more than two attributes. daisyUI's popover mode expects `class="dropdown"` on the `[popover]` element itself, plus `anchor-name` / `position-anchor` styles.
- The installed CSS has `&[popover]{position:fixed; @supports not (position-area:bottom){margin:auto}}`. Without CSS anchor positioning, the menu opens centred in the viewport, not under the button. Anchor positioning only arrived in Safari 26 / iOS 26. So the fix targets Safari users, and Safari users are the ones who get the misplaced menu. That is better than a menu that never opens, but it is not a clean fix.
- Prod and security risk is low: the change touches only a template and a static file. Deploying it still needs a CSS rebuild (`npm run build:css:prod`, because Tailwind/daisyUI tree-shake classes from templates) and `collectstatic`.

## Better proposal
- **Lowest risk (S, about 5 min):** in `mobile-menu.js:10`, toggle `dropdown-open` on `button.parentElement` instead of `hidden`. Remove `hidden` from `base.html:42`. Guard Escape with `if (button.getAttribute("aria-expanded") !== "true") return;`. This works the same in every browser.
- **Removing the JS (S):** use `<details class="dropdown"><summary class="btn btn-ghost btn-circle">`. The installed CSS exempts `details` from the hide rule, it is native in every Safari, it needs no anchor positioning, and it exposes the expanded state natively. You give up click-outside closing, which matters little because every item navigates away. `mobile-menu.js` and its script tag (`base.html:11`) can then be deleted.
- Use popover only once you no longer need to support iOS below 26.
- Whichever option you choose, test it in Playwright WebKit or on an iPhone before merging.

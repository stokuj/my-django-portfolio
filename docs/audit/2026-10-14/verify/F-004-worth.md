# F-004 (worth lens): Mobile menu likely never opens in Safari/iOS; JS reimplements native popover

**Verdict:** CONFIRMED (not run in a browser)
**Confidence:** medium
**Adjusted severity:** high (stays high: on phones below `md`, this menu is the only nav. `base.html:54` hides the desktop links with `hidden md:flex`)

## Reasoning
- `base.html:24-46`: the mobile menu uses the `.dropdown` focus pattern with a real `<button>` (`base.html:25`). The `ul.dropdown-content` starts with Tailwind `hidden` (`base.html:40`).
- `mobile-menu.js:9-12` only toggles `hidden` and `aria-expanded`. It never adds `dropdown-open` and never moves focus into the dropdown.
- daisyUI v5 (`package.json:9`, `^5.0.28`) keeps `.dropdown-content` hidden unless the dropdown has focus or `.dropdown-open`. The daisyUI dropdown docs ("Method 3. CSS focus") say plainly that Safari does not focus `<button>` on click (WebKit bug 22261), which is why they use `div tabindex=0 role=button`. In Chrome the click focuses the button, so the menu appears there, which would explain why nobody noticed. In Safari/iOS, removing `hidden` is not enough, so the menu stays invisible.
- Smaller issues (I did not run them, but they follow from the code): tabbing out triggers `:focus-within` loss and hides the menu while `aria-expanded` stays `"true"`. `mobile-menu.js:27-31` calls `button.focus()` on every Escape press anywhere on the page, even when the menu is closed.
- No deliberate decision blocks the change. `aa8388f` added the JS as a general a11y pass, and `docs/frontend.md:26` only lists the file. No test references `mobile-menu`.

## Is the proposed fix worth it / simplest?
Yes. Native `popover` + `popovertarget` gives toggle, light-dismiss (outside click), Escape, focus return and `aria-expanded` for free. It deletes `mobile-menu.js` (39 lines) and its `<script>` tag (`base.html:11`), so the diff shrinks overall. daisyUI v5 documents this as dropdown "Method 2".

Caveat on the risk note: Safari before 26 has popover but no CSS anchor positioning. The menu then renders with the UA popover default (top layer, centered). That is still usable, so the risk is cosmetic, not a broken menu. Fix links still need to close the popover after navigation, but full page loads already do that.

## Better / alternative proposal
- Preferred (as proposed): `<button popovertarget="mobile-menu" style="anchor-name:--nav">` + `<ul id="mobile-menu" popover class="dropdown menu ..." style="position-anchor:--nav">`. Drop `hidden`, drop `mobile-menu.js`.
- If the old-Safari centered fallback is unacceptable: `<details class="dropdown"><summary class="btn ...">`. It is native in every Safari and needs no anchor positioning. The cost is no outside-click close, and `aria-expanded` is handled natively.
- Smallest patch if JS is kept: toggle `dropdown-open` on the parent `.dropdown` instead of (or with) `hidden` in `mobile-menu.js:10`, and guard the Escape handler with an `isOpen` check. This fixes Safari but keeps the 39 lines.

# F-004: Mobile menu likely never opens in Safari/iOS; JS reimplements native popover

**Lens:** reproduce
**Verdict:** CONFIRMED (not run in a browser)
**Confidence:** medium
**Adjusted severity:** high (kept)

## Reasoning
- `django/main/templates/base.html:25` wraps the menu in `.dropdown`. The trigger is a real `<button>` (`base.html:26-33`) and the `<ul>` has `dropdown-content hidden` (`base.html:40-42`). The wrapper has no `dropdown-open` class, and neither the template nor the JS ever adds it.
- `django/main/static/js/mobile-menu.js:9-12` only toggles the Tailwind `hidden` class and `aria-expanded`.
- `package.json` pins `daisyui ^5.0.28`, and `input.css` does not override `.dropdown`. The daisyUI v5 docs (Method 3, "CSS focus") say the content is displayed only while the trigger has focus, or when `.dropdown-open` is set. They also say Safari does not focus `<button>` on click (WebKit bug 22261), which is why daisyUI uses `div tabindex=0 role=button` for this method. So in Safari, removing `hidden` leaves the content hidden by daisyUI's own rule. In Chromium and Firefox, a click focuses the button, so the menu works there, which can hide the bug.
- Below `md`, the centre nav links are hidden (`base.html:54`, `hidden md:flex`), so on phones this menu is the only site navigation. On iOS that navigation is lost, so high severity holds.
- The secondary claims hold:
  - When focus leaves the dropdown, daisyUI hides the content but the JS state stays open, so `aria-expanded="true"` is stale and the next click "closes" a menu that is already invisible. It takes two taps to reopen.
  - The Escape handler (`mobile-menu.js:27-32`) runs on every Escape anywhere on the page and calls `button.focus()` with no check that the menu is open, which steals focus on mobile widths.
- Limit: the Safari behaviour comes from daisyUI's documentation and the WebKit bug. I did not reproduce it in WebKit, and I did not inspect the compiled CSS because `style.css` is off-limits.

## Better proposal
The proposal is valid but incomplete. With daisyUI v5's popover method, the `dropdown` class goes on the `<ul popover>` itself, not on a wrapper, and you also need `anchor-name` / `position-anchor` styles. Safari before 26 has no CSS anchor positioning, so on older iOS the popover opens in the wrong place. That is exactly the platform this fix is for.

Lowest-risk fix (effort S): keep the markup and change the JS to toggle `dropdown-open` on the `.dropdown` wrapper, alongside or instead of `hidden`. Also guard the Escape handler with `if (button.getAttribute("aria-expanded") !== "true") return;`. This works in every browser without anchor positioning.

Switch to `popover` + `popovertarget` (which gives Escape and light-dismiss natively, so `mobile-menu.js` can be deleted) only if older iOS support is not needed or is tested.

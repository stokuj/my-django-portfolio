# F-079 — Navbar breakpoints mismatch (both menus visible at md)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/templates/base.html:25` — hamburger dropdown wrapper is `dropdown lg:hidden`, so it shows below 1024px.
- `django/main/templates/base.html:54` — desktop links are `hidden md:flex`, so they show from 768px up.
- No custom breakpoints: no `tailwind.config.*`, and `django/main/static/src/css/input.css` has no `@theme`/`--breakpoint` overrides. Tailwind v4 defaults apply (`package.json:10`), md = 768px, lg = 1024px.
- Result: from 768px to 1023px both the hamburger button and the inline Home/My Projects/About links render. The two navs are redundant, not broken. Purely cosmetic.

## Better proposal
Change `lg:hidden` to `md:hidden` at `base.html:25` (one token). That keeps the inline links at md+, which fit at 768px (three `btn-ghost text-xl` links). Alternatively, change line 54 to `hidden lg:flex` if the links feel crowded at md alongside the site name and the social/theme icons.

# frontend

Scope: `django/main/templates/**`, `django/main/static/js/*.js`, `django/main/static/src/css/input.css` (Tailwind v4 CSS config, no tailwind.config.js), `package.json`, plus `infra/Caddyfile` for asset delivery. Heading cascade verified by building the CSS into /tmp.

## 1. Mobile menu probably never opens in Safari/iOS
- Severity: high | Category: bug | Effort: S | Verdict: PLAUSIBLE (not run in Safari)
- File: `django/main/templates/base.html:25-42`, `django/main/static/js/mobile-menu.js:6-9,27-32`
- Problem: the menu sits inside daisyUI `.dropdown`, and daisyUI v5 sets `display:none` on `.dropdown:not(:focus-within, .dropdown-open) .dropdown-content`. The JS only removes `hidden` and never adds `dropdown-open`. Safari (macOS and iOS) does not focus a `<button>` when it is clicked, so `:focus-within` never matches and the `<ul>` stays hidden. Other browsers have their own problem: tabbing out of the menu hides it while `aria-expanded` stays `true`. Separately, the global Escape handler always calls `button.focus()`, even when the menu is closed, so pressing Esc in the search box on mobile moves focus to the hamburger.
- Proposal: use the native popover. Give the `<ul>` `popover` and the button `popovertarget="mobile-menu"`, which daisyUI v5 supports for `.dropdown`. This gives Esc to close, closing on an outside click, and correct state without any JS, so `mobile-menu.js` can be deleted. If you keep the JS, toggle `dropdown-open` instead of `hidden` and only move focus on Esc when the menu is open.
- Risk: low. Check on iOS Safari after the change.

## 2. Global h1/h2/h3 rules sit outside any layer and override all Tailwind font sizes
- Severity: medium | Category: bug | Effort: S
- File: `django/main/static/src/css/input.css:9-17`
- Problem: Tailwind v4 puts utilities and components in `@layer`, but these rules are unlayered (in the built CSS they come after `@layer utilities`, with no layer). Unlayered rules always win. As a result: `text-3xl sm:text-4xl` (about_content.html:2) is always 4xl. `sm:text-5xl` (error_404_content.html:3) never applies. The projects h1 `text-2xl sm:text-3xl` (projects_content.html:1) shows at 4xl. `text-2xl` h2s (home.html:10, base.html:119) show at xl. The card-title `text-lg` (project_card.html:34) shows at xl. `.md-article h1/h2/h3` sizes (input.css:52-62) are overridden.
- Proposal: wrap these rules in `@layer base { ... }`.
- Risk: headings will render at their intended sizes, which will look different from now. Check the pages visually.

## 3. Every page except the error pages has the title "My Portfolio"
- Severity: medium | Category: bug | Effort: S
- File: `django/main/templates/pages/about.html:3`, `django/main/templates/projects/detail.html:4`, `base.html:8`
- Problem: about and detail override `{% block page_name %}`, which does not exist in base.html (base only has `title`). home.html and projects/index.html set no title. This hurts SEO, makes browser tabs and history indistinguishable, and fails WCAG 2.4.2.
- Proposal: rename to `{% block title %}` and add titles to home and projects (for example `{{ project.title }} | {{ site_name }}`).
- Risk: none.

## 4. Project grid hidden until JS runs, behind a fake skeleton
- Severity: medium | Category: frontend | Effort: S
- File: `django/main/templates/projects/index.html:40-62`, `django/main/static/js/projects-filters.js:88-89`
- Problem: the cards are rendered on the server, but `#projectGrid` starts as `hidden` and only shows after `DOMContentLoaded`. If JS fails, is blocked or is disabled, users and crawlers only see 6 skeleton cards. The skeleton also stands in for a load that never happens.
- Proposal: delete the skeleton markup and the `hidden` class on the grid, and delete the two lines at the end of the JS.
- Risk: none.

## 5. MathJax loaded from CDN with a floating version, no SRI and no CSP
- Severity: medium | Category: security | Effort: S
- File: `django/main/templates/projects/detail.html:52`, `infra/Caddyfile` (no security headers), `django/config/` (no CSP)
- Problem: `cdn.jsdelivr.net/npm/mathjax@3/...` follows whatever version is latest in 3.x, has no `integrity` or `crossorigin`, and no CSP limits it. If the CDN or npm package is compromised, that script runs on the site's origin, including for staff users who have admin sessions. It also loads on every detail page, even when the README has no math.
- Proposal: pin an exact version and add `integrity` and `crossorigin="anonymous"`, or serve the file from `static/`. Load it only when the HTML contains `class="arithmatex"`. A CSP is a separate step later.
- Risk: low.

## 6. Dark mode ignores OS preference, flashes light, and pins light on first visit
- Severity: medium | Category: frontend | Effort: S
- File: `django/main/static/js/theme-toggle.js:1,7,32-35`, `base.html:3,7,10`, `input.css:107-108,144`
- Problem: the theme is applied after `DOMContentLoaded` from a `defer` script, so users who chose dark see a light flash on every page load. Both themes set `prefersdark: false`, and on the first visit the script writes `fantasy3` to localStorage, so `prefers-color-scheme: dark` is never respected. `localStorage` calls have no try/catch, so if storage is blocked the script throws and the toggle stops working.
- Proposal: set `prefersdark: true` on dim2 and only write localStorage when the user toggles. Move the 3-line "read saved theme, set data-theme" into an inline `<script>` in `<head>` before the stylesheet, and wrap the storage calls in try/catch.
- Risk: low. Visitors who have never chosen a theme and use OS dark mode will now see dark.

## 7. Navbar breakpoints mismatch (hamburger and desktop links both visible at md)
- Severity: low | Category: bug | Effort: S
- File: `django/main/templates/base.html:25,54`
- Problem: the dropdown uses `lg:hidden` but the desktop links use `hidden md:flex`, so from 768 to 1023px both show and the nav is duplicated.
- Proposal: use the same breakpoint for both (for example `md:hidden`).
- Risk: none.

## 8. Timeline accordion uses unlabelled radio inputs
- Severity: low | Category: frontend | Effort: S
- File: `django/main/templates/components/timeline_section.html:1-3`
- Problem: each `<input type="radio" name="timeline-accordion">` has no label, so screen readers announce "radio button, not checked" with no name. The title is a plain `<div>`.
- Proposal: use `<details class="collapse collapse-plus" name="timeline-accordion" {% if section.checked %}open{% endif %}>` with `<summary class="collapse-title">`. daisyUI v5 supports this, and it gives native accessibility and the exclusive-accordion behaviour.
- Risk: low.

## 9. Tag filter state is shown only by color
- Severity: low | Category: frontend | Effort: S
- File: `django/main/templates/projects/index.html:33-35`, `django/main/static/js/projects-filters.js:74-82`
- Problem: the active tag is shown only by swapping `btn-primary` and `btn-outline`. There is no `aria-pressed`, so assistive tech cannot tell which filter is on.
- Proposal: set `aria-pressed="true|false"` in the same loop, starting with `true` on "All Projects". Also make `#searchInput` `type="search"`.
- Risk: none.

## 10. Heatmap is not accessible
- Severity: low | Category: frontend | Effort: S
- File: `django/main/templates/pages/about.html:53,82,401-421`
- Problem: about 371 generic `<div>` cells each get an `aria-label`. ARIA does not allow `aria-label` on a generic role, so most screen readers ignore it. The grid has no name or summary, and the "Loading..." status is not a live region.
- Proposal: give `#heatmap-minimal-grid` `role="img"` with an `aria-label` that summarises the totals, mark the cells `aria-hidden="true"` (keep `title` for mouse users), and add `aria-live="polite"` to the status `<p>`.
- Risk: none.

## 11. Heatmap inline script is over-generalised
- Severity: low | Category: simplification | Effort: M
- File: `django/main/templates/pages/about.html:257-464`
- Problem: about 200 lines of inline JS are built around a `variantConfigs` array with exactly one entry, a filter over 9 element lookups, and a `tooltipMode === "daisy"` branch that is never used (about.html:422-424). Because the script is inline and has template interpolation, a strict CSP is not possible.
- Proposal: move it to `static/js/heatmap.js`, drop the variant layer and the dead branch, and pass `heatmap_enabled` and the URL as `data-*` attributes on the section.
- Risk: low. Check by loading the heatmap on the about page.

## 12. Heavy hero background PNGs, mostly covered by an overlay; one image unused
- Severity: low | Category: performance | Effort: S
- File: `django/main/templates/components/hero_section.html:2`, `pages/home.html:6`, `django/main/static/images/`
- Problem: `hero-bg.png` (3.0 MB) loads on the home page and `hero-bg2.png` (1.3 MB) on the other pages. Both sit under an 85-90% opaque `bg-base-100` overlay. `hero-bg3.png` (1.5 MB) is not referenced anywhere.
- Proposal: re-encode to WebP or AVIF at about 1600px wide (well under 200 KB) and delete `hero-bg3.png`.
- Risk: none.

## 13. Dead classes and an unused dependency
- Severity: low | Category: simplification | Effort: S
- File: `base.html:42` (`menu-compact`), `base.html:165` (`hover:bg-primary-focus`), `projects/detail.html:9,26` (`prose`, `not-prose`), `package.json:13` (`@catppuccin/daisyui`)
- Problem: `menu-compact` and `primary-focus` are pre-v4 daisyUI names and produce no CSS (0 matches in the built CSS). `@tailwindcss/typography` is not installed, so `prose` only sets unused variables. `@catppuccin/daisyui` is not referenced anywhere.
- Proposal: delete them.
- Risk: none.

## 14. Template duplication
- Severity: low | Category: simplification | Effort: S
- File: `projects/components/project_card.html:9-29`, `pages/about.html:143-151,207-215`, `base.html:63-78,127-145`
- Problem: two `<img>` blocks that differ only in `src` and `alt`. The status-badge if/elif chain is copied twice. The GitHub and LinkedIn icon buttons are written out twice (navbar and footer).
- Proposal: use one `<img>` with `{% if %}` on `src`, and a `components/status_badge.html` include. The social buttons can stay as they are, or become one include that takes classes.
- Risk: none.

## 15. MathJax `$` delimiters can turn stray dollar signs into math
- Severity: low | Category: bug | Effort: S | Verdict: PLAUSIBLE
- File: `django/main/static/js/mathjax-config.js:3-6`, `django/main/views.py:362-369`
- Problem: `pymdownx.arithmatex` with `generic: True` already outputs `\(...\)` inside `span.arithmatex`, but MathJax also scans the whole page for `$...$`. README text such as "costs $5 to $10" can be typeset as math.
- Proposal: follow the pymdownx docs: drop the `$` and `$$` delimiters and set `options: { ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex" }`.
- Risk: low. Check one README that contains math.

## 16. Nav and footer semantics
- Severity: low | Category: frontend | Effort: S
- File: `base.html:55-57,94,152-159,167`
- Problem: nav links have no `aria-current="page"`. Flash messages have no `role="status"`. The footer links to `projects` twice ("My projects" and "Projects") and has 3 mailto links. The decorative arrow SVG has no `aria-hidden`.
- Proposal: add `aria-current` with a `request.resolver_match.url_name` check, add `role="status"` to the alerts, remove the duplicate links, and add `aria-hidden="true"` to the SVG.
- Risk: none.

## 17. Static assets served uncompressed and without cache headers
- Severity: low | Category: performance | Effort: M
- File: `infra/Caddyfile:16-30`, `django/config/settings.py:181`
- Problem: Caddy has no `encode zstd gzip` and no `Cache-Control` on `/static/*`. Static file names are not hashed (`StaticFilesStorage`), so they cannot be cached for long safely.
- Proposal: add `encode zstd gzip` to the site block. Switch to `ManifestStaticFilesStorage` and add `header /static/* Cache-Control "public, max-age=31536000, immutable"`.
- Risk: the manifest storage fails on missing references during `collectstatic`. Run it in CI first.

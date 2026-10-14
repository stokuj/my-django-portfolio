# sec-markdown

Scope: markdown -> HTML pipeline (`django/main/views.py` bleach allowlist, `projects/detail.html` `|safe`), MathJax config/loader, trust of README content fetched by `markdown_sync.py`. Probes were run against `_render_markdown_to_html` at HEAD.

Verified OK (no finding): `javascript:`/`data:` hrefs are stripped (protocols = http/https/mailto, applied after the callable attr filter); `on*` attributes and `<script>` are stripped; `target` is not allowed, so no reverse-tabnabbing; `img src` is limited to GitHub prefixes; `<math>` tags are stripped. `|safe` is used only at `detail.html:18` on bleach output.

Trust model: README text from `raw.githubusercontent.com` (`markdown_sync.py:68-96`, owner/repo taken from admin-set `project.github_url`, any GitHub owner) is stored verbatim and rendered with raw HTML enabled. Anyone with push access to those repos controls page content, bounded only by the bleach allowlist and MathJax below.

---

## 1. MathJax typesets sanitized text without the `safe` extension (`\href{javascript:...}`, `\style`)
- Severity: medium
- Category: security
- File: django/main/static/js/mathjax-config.js:1 (loader: django/main/templates/projects/detail.html:52)
- Problem: bleach runs server-side, MathJax runs after it in the browser. `$\href{javascript:alert(1)}{click}$` survives bleach unchanged (verified: `<span class="arithmatex">\(\href{javascript:alert(1)}{click}\)</span>`). The config does not load `ui/safe`, which is the MathJax mechanism that filters `\href` protocols and `\style`/`\class`/`\cssId`. MathJax 3 combined components do not load it by default (per MathJax docs, not executed in a browser here), so a README can yield a clickable `javascript:` link / arbitrary inline CSS. Also, MathJax scans the whole page, not only `.arithmatex` nodes.
- Proposal: in `mathjax-config.js` add `loader: {load: ['ui/safe']}` and restrict processing to Arithmatex output: `options: {ignoreHtmlClass: '.*|', processHtmlClass: 'arithmatex'}`.
- Effort: S
- Risk: Low; only Arithmatex spans get typeset (intended).

## 2. MathJax loaded from CDN with floating major version, no SRI, no CSP
- Severity: medium
- Category: security
- File: django/main/templates/projects/detail.html:52
- Problem: `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js` resolves to whatever 3.x is latest, with no `integrity`/`crossorigin`. No Content-Security-Policy is set anywhere (`settings.py` has none, `infra/Caddyfile` adds no headers). A CDN/package compromise runs arbitrary JS on the site origin (incl. admin sessions viewing blog pages).
- Proposal: pin an exact version (e.g. `mathjax@3.2.2`) and add `integrity="sha384-..." crossorigin="anonymous"`, or vendor the file into `static/`. Optionally add a CSP later.
- Effort: S
- Risk: Low; pinning freezes updates (intended).

## 3. Unrestricted `class` on `div`/`span` allows page-overlay UI redressing
- Severity: low
- Category: security
- File: django/main/views.py:64
- Problem: `"div": ["class"]`, `"span": ["class"]` accept any value; raw HTML in README passes through Python-Markdown. Verified: `<div class="fixed inset-0 z-50 bg-black">overlay</div>` is emitted unchanged, so README content can use the site's Tailwind/daisyUI classes to cover the page or fake site UI. The only class the pipeline needs is `arithmatex`.
- Proposal: in `_clean_attributes` (views.py:77) allow `class` only when `value == "arithmatex"`.
- Effort: S
- Risk: Breaks any README that relies on custom classes (none expected; CSS targets `.md-article` descendants).

## 4. MathJax `$...$` inline delimiter typesets dollar amounts anywhere on the page
- Severity: low
- Category: bug
- File: django/main/static/js/mathjax-config.js:3
- Problem: Arithmatex `generic: True` already converts math to `\(...\)`/`\[...\]` and leaves non-math dollars as text (verified: `Price $5 and $10 here` stays plain). MathJax then re-scans with `["$", "$"]`, so client-side `5 and ` is rendered as math. `$`/`$$` delimiters are redundant with Arithmatex output.
- Proposal: drop the `$`/`$$` entries (or fix via finding 1's `processHtmlClass: 'arithmatex'`, which removes the scan of non-math text).
- Effort: S
- Risk: None if finding 1 is applied.

## 5. No tests pin protocol stripping or class allowlist
- Severity: low
- Category: tests
- File: django/main/tests/test_views.py:396
- Problem: Tests cover `<script>`, `onerror`, and external `img src`, but nothing asserts `javascript:`/`data:` hrefs are removed or that `class` is restricted. A change to `ALLOWED_MARKDOWN_PROTOCOLS` or the attr filter would go unnoticed.
- Proposal: one parametrized test feeding `[x](javascript:alert(1))`, `<a href="data:...">`, `<div class="fixed">` and asserting the dangerous parts are absent.
- Effort: S
- Risk: None.

## 6. bleach is deprecated upstream
- Severity: low
- Category: library
- File: pyproject.toml:8
- Problem: `bleach==6.2.0`; bleach was declared deprecated by Mozilla (security fixes only, html5lib unmaintained). The sanitizer is the only server-side XSS barrier for this page.
- Proposal: plan a move to `nh3` (`nh3.clean(html, tags=..., attributes=..., url_schemes=..., attribute_filter=...)`), which maps 1:1 onto the current config.
- Effort: S
- Risk: Minor output differences; existing sanitizer tests cover them.

## 7. Outbound links get no `rel="nofollow noopener"`
- Severity: low
- Category: security
- File: django/main/views.py:371
- Problem: `bleach.clean` does not add `rel`; README links render as plain `<a href>`. No tabnabbing risk (no `target`), but third-party links get full SEO weight and referrer.
- Proposal: optional; set `rel` via nh3 `link_rel="nofollow noopener noreferrer"` if migrating (finding 6), otherwise skip.
- Effort: S
- Risk: None.

# F-035 — MathJax from CDN with floating version, no SRI, and no CSP anywhere

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (unchanged)

## Reasoning

- `django/main/templates/projects/detail.html:52` loads `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js` with `async`. There is no `integrity` or `crossorigin` attribute. `@3` is a semver range, so jsDelivr serves the latest 3.x.
- The `extra_scripts` block (detail.html:50-53) is unconditional. `blog_detail` (`django/main/views.py:401-410`) renders it for every blog project, whether or not the markdown has math.
- Grepping the templates finds no `integrity` or `crossorigin` anywhere. This is the only external `<script src="http...">`.
- There is no CSP. `django/config/settings.py:57-65` has no CSP middleware, and only SecurityMiddleware/HSTS settings are configured (`settings.py:101-105`). `infra/Caddyfile` sets no `header` directive at all.
- Inline `<script>` blocks exist at `django/main/templates/pages/about.html:258` and `:468`. A strict CSP would need nonces/hashes or externalising them.
- The attack path is reachable but needs a precondition: compromise of the jsDelivr CDN or of the `mathjax` npm publisher (a new 3.x release). The script runs same-origin, so it can make authenticated same-origin requests in a staff session (CSRF token readable from DOM/cookie). Since this is not directly exploitable, medium fits better than high.

## Nuances

- Math rendering depends on `pymdownx.arithmatex` with `generic: True` (`views.py:364-368`), which emits `class="arithmatex"`. A conditional load can key off that string in `markdown_html`.
- SRI covers only the entry script. `tex-mml-chtml` fetches its fonts from the same CDN, so a future CSP needs `font-src cdn.jsdelivr.net` (or vendored fonts).

## Better proposal

1. Pin `mathjax@3.2.2` and add `integrity="sha384-..."` and `crossorigin="anonymous"`. The alternative is vendoring into `static/`, which also removes the third-party origin. Effort S.
2. Wrap the block in `{% if markdown_html and 'arithmatex' in markdown_html %}`. Effort S.
3. Add CSP as a separate, later item: a Caddy `header Content-Security-Policy-Report-Only ...` line first. The project is on Django 5.1.15 (`pyproject.toml:10`), so it has no built-in CSP; Caddy headers are the dependency-free option.

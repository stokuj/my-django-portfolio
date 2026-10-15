# F-035 (worth): MathJax from CDN with floating version, no SRI, and no CSP anywhere

**Verdict:** CONFIRMED (core). Proposal trimmed.
**Confidence:** high
**Adjusted severity:** medium (keep). Effort: S.

## Verified
- `django/main/templates/projects/detail.html:52` loads `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js` with a floating `@3` and no `integrity`/`crossorigin`.
- No CSP anywhere: `django/config/settings.py:101-105` sets only SSL redirect/HSTS/proxy header. `infra/Caddyfile` has no `header` directive. No `django-csp`.
- Inline scripts at `django/main/templates/pages/about.html:258` and `:468`.
- MathJax is needed. Markdown uses `pymdownx.arithmatex` with `generic: True` (`django/main/views.py:364-368`). Bleach keeps `class` on span/div (`views.py:62-67`). Added on purpose in commit 6d91a42. No doc rejects pinning.

## Worth / correctness of the proposal
1. **Pin + SRI is worth doing.** It is a 1-line change. A floating `@3` means jsDelivr serves any newly published 3.x, which is the realistic supply-chain path. An exact npm version is immutable.
   - Caveat: SRI covers only the entry script. `tex-mml-chtml` autoloads TeX extensions (e.g. `[tex]/mhchem`) and fonts from the same CDN base without SRI. Pinning still fixes the version of those files, so pinning is the bigger win.
   - Caveat: `django/main/tests/test_views.py:492-494` asserts the substring `mathjax@3/es5/tex-mml-chtml.js`. `mathjax@3.2.2/es5/...` does not contain it, so update the test in the same diff.
2. **Vendoring:** a valid alternative, but it adds an approx. 1 MB+ bundle plus font/extension assets to the repo, and MathJax autoload must be pointed at the local path. That is more work than pin + SRI for no extra gain. Skip it.
3. **Conditional load (only when `class="arithmatex"` is present):** this is a performance nicety, not a security fix, so it is scope creep for this finding. It would also break `test_blog_detail_includes_mathjax_assets` (`test_views.py:487-494`), whose fixture project has no math. Drop it or file it separately.
4. **CSP:** a separate, larger item, not an S fix. It would need nonces or moving the inline scripts out of `about.html:258,468`, the admin tooling and Caddy/django-csp config. Track it as its own finding (report-only first). Do not bundle it here.

## Better proposal (smallest diff)
```html
<script src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"
        integrity="sha384-<hash of that exact file>" crossorigin="anonymous"
        id="MathJax-script" async></script>
```
Then update the asserted substring at `test_views.py:493`. Leave CSP and conditional loading for separate findings.

# F-027 — MathJax typesets sanitized text without ui/safe (\href{javascript:})

**Verdict:** CONFIRMED (reproduce lens)
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/main/views.py:357-377` renders README markdown with `pymdownx.arithmatex` (generic) then `bleach.clean`. `span[class]` is allowed (`views.py:62-67`), and the TeX body is plain text, so bleach leaves it intact.
- Reproduced at HEAD via `_render_markdown_to_html("Hi $\href{javascript:alert(1)}{click}$ ...")`, which gives
  `<span class="arithmatex">\(\href{javascript:alert(1)}{click}\)</span>`. `\style{...}` passes through the same way.
- `django/main/templates/projects/detail.html:51-52` loads `js/mathjax-config.js` plus `mathjax@3/es5/tex-mml-chtml.js`. The config (`mathjax-config.js:1-23`) has no `loader.load` and no `processHtmlClass`/`ignoreHtmlClass`, so MathJax scans the whole page.
- Checked the CDN bundle: the `html` package (`href`, `class`, `style`, `cssId`) is autoloaded. CHTML `createCHTMLnode` emits `<a href=e>` with no filtering. The string `safe` does not appear in the bundle, so ui/safe is not included.
- Result: the rendered page contains a clickable `javascript:` link, which bypasses the `ALLOWED_MARKDOWN_PROTOCOLS` allowlist (`views.py:68`).

## Why the severity is lower
- Content source: READMEs are fetched from the GitHub repos the admin configured (`markdown_sync.py:34-64`, `project.github_url`). An attacker needs write access to the owner's repo README, or a merged PR.
- A user click is required. `\style`/`\class` only allow visual redressing.
- This is a real defense-in-depth gap in a sanitizer that exists on purpose. It is not something an anonymous user can exploit.

## Better proposal
The proposal as given is correct. In `mathjax-config.js`:
```js
loader: { load: ["ui/safe"] },
options: { ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex", skipHtmlTags: [...] },
```
Optionally drop the `$`/`$$` delimiters: with arithmatex `generic: true` the output always uses `\(..\)`/`\[..\]`. Add a view test asserting the config contains `ui/safe`. Effort S.

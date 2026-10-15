# F-073 (reproduce): $...$ delimiters typeset dollar amounts anywhere on the page

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (cosmetic rendering bug, not security)

## Reasoning
- `django/main/views.py:362-369` renders README markdown with `pymdownx.arithmatex` in `generic: True` mode. Real math (`$x^2$`) becomes `<span class="arithmatex">\(x^2\)</span>`, so the server already converts it to `\(..\)`/`\[..\]`.
- Arithmatex's smart-dollar rule leaves currency text alone. Checked at HEAD: `"It costs $5 and $10 total."` comes out as `<p>It costs $5 and $10 total.</p>`, with the dollar signs still plain text.
- `django/main/static/js/mathjax-config.js:3-10` still turns on `["$","$"]` and `["$$","$$"]` as client-side delimiters. No `processHtmlClass`/`ignoreHtmlClass` is set (lines 13-22), so MathJax scans the whole document body, including the sidebars and footer. MathJax's `$` matching has no whitespace rule, so `$5 and $` is typeset as math ("5 and" in italic math font).
- `projects/detail.html:51-52` is the only page that loads the config, so the issue is limited to the project detail pages. `pre`/`code` are skipped (config lines 14-21), so fenced code is not affected.

## Better proposal
Use the MathJax 3 config that the Arithmatex docs give for generic mode:
```js
tex: { inlineMath: [["\\(","\\)"]], displayMath: [["\\[","\\]"]], processEscapes: true, processEnvironments: true },
options: { ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex" }
```
`processHtmlClass` has no effect by itself. It only restricts scanning when `ignoreHtmlClass` is also set. Effort S.

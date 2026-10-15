# F-042 (reproduce lens): No negative tests for the markdown sanitizer (XSS boundary)

- Verdict: CONFIRMED (test gap is real). Severity adjusted: medium -> low.
- Confidence: high

## Reasoning
- `_render_markdown_to_html` (django/main/views.py:357-377) runs `bleach.clean` with the tag allowlist (views.py:33-60), the `_clean_attributes` callable (views.py:77-87) and protocols `http/https/mailto` (views.py:68). Its output is rendered with `|safe` (django/main/templates/projects/detail.html:18).
- Existing negative tests only cover `<script>` (test_views.py:396-414), `img onerror` (test_views.py:416-436) and an external img host (test_views.py:613-630). `test_blog_detail_keeps_safe_markdown_elements` (438-464) is a positive test. Grep finds no test for `javascript:`/`data:` hrefs, `onclick`/`style`, `iframe`/`svg`/`form`, look-alike hosts, or the `class` allowlist. The gap is exactly as described.
- The sanitizer behaves correctly at HEAD. I ran `_render_markdown_to_html` on these inputs:
  - `[x](javascript:alert(1))`, `[x](data:...)` and mixed-case `JaVaScRiPt:` with onclick/style each returned `<a>x</a>`, with the href and handlers removed.
  - `iframe`, `svg onload` and `form` were stripped.
  - `https://github.com.evil.tld/x.png` returned `<img alt="a">` with no src. The trailing `/` in `_GITHUB_IMG_PREFIXES` (views.py:70-74) blocks look-alike hosts.
  - `div class="foo" style=...` kept `class` and dropped `style`.
- So nothing can be exploited today. This is only missing regression protection for an XSS boundary. The markdown comes from the owner's GitHub READMEs or an admin upload, which further lowers the risk. "Low" (nice to have) fits better than "medium".
- Minor: arbitrary `class` values on div/span are allowed by design (needed for `arithmatex`, test_views.py:484). That allows CSS-class spoofing but not XSS.

## Better proposal
Add one test method to the existing view tests that calls `_render_markdown_to_html` directly, using `subTest` over the payloads above. Assert that `javascript:`, `data:`, `on*=`, `style=`, `<iframe`, `<svg`, `<form` and `evil.tld` are absent. Effort: S.

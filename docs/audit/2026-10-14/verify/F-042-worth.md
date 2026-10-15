# F-042 (worth lens): No negative tests for the markdown sanitizer (XSS boundary)

**Verdict:** CONFIRMED (gap is real), but downgraded and the proposal needs trimming
**Confidence:** high
**Adjusted severity:** low (was medium)

## Verified at HEAD
- Output rendered with `|safe`: `django/main/templates/projects/detail.html:18`.
- Sanitizer: `bleach.clean` with tag list `django/main/views.py:33-61`, attrs `:62-67`, protocols `:68`, custom filter `_clean_attributes` `:77-87`, call `:357-378`.
- Existing tests: `<script>` (`django/main/tests/test_views.py:396-414`), img `onerror` (`:416-436`), external img src (`:613-630`). No test for `javascript:`/`data:` href, `on*`/`style`, iframe/svg/form, or look-alike img host.

## Why low, not medium
- Ran every proposed payload through `_render_markdown_to_html` (read-only shell): `javascript:` and `data:` hrefs dropped, `onclick`/`style` dropped, iframe/svg/form stripped, `https://github.com.evil.tld/...` img src dropped (prefixes end in `/`, `views.py:70-74`). No current bug; this is regression-guard value only.
- Markdown comes from the owner's own GitHub repos (`django/main/markdown_sync.py:68-76`) or admin upload; attacker reach is limited.
- `javascript:`/`data:` filtering is bleach's own protocol check (bleach 6.2.0); the project only owns the lists and `_clean_attributes`.

## Proposal is partly wrong
- "class allowlist" does not exist: `class` is allowed with any value on `div`/`span` (`views.py:64,66`). `<div class="fixed inset-0 z-50">` passes through unchanged. A test asserting it is removed would fail. If arbitrary Tailwind classes (UI-redress overlay) matter, that is a separate low security finding, not a test gap. Note `pymdownx.arithmatex` needs `class="arithmatex"` (`test_views.py:484`), so any class filter must keep it.

## Better proposal
Extend the existing `test_blog_detail_strips_external_img_src`-style coverage, or add one `SimpleTestCase` with `subTest` calling `_render_markdown_to_html` for 4 payloads that exercise project config: `[x](javascript:alert(1))`, `<a onclick=x style=y>`, `<iframe>`, `<img src="https://github.com.evil.tld/a.png">`. Assert the token is absent. Skip the class case. Effort S.

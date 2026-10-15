# F-087 — Audit spec 1b/2a paths without tests (markdown_file cleanup, camo/github images)

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning

- Spec 1b (`docs/superpowers/specs/2026-05-14-codebase-audit-design.md:30-34`) covers both `thumbnail` and `markdown_file`.
  Code handles both: `django/main/models.py:248` (post_delete) and `django/main/models.py:261-262` (pre_save).
- Tests cover only thumbnail: `django/main/tests/test_models.py:289` (delete) and `:300` (replace).
  No test anywhere asserts the old/deleted `markdown_file` is removed from storage (grep over `django/main/tests/`).
- Partial indirect coverage: `test_markdown_sync.py:50-72` drives `markdown_sync.py:168-172`, which replaces `markdown_file`
  and fires the pre_save cleanup, but it asserts only the new content, not that the old file is gone.
- Spec 2a allows three prefixes; code matches: `django/main/views.py:70-74` (`github.com`, `raw.githubusercontent.com`, `camo.githubusercontent.com`).
  Tests assert only `raw.githubusercontent.com`: `test_views.py:434` and `test_views.py:630` (finding cited 613; the test starts at 613, assert at 630).
  `camo.` and `github.com/` prefixes are untested. Spec manual check `:152` explicitly says "github.com img -> passes".

## Proposal

Agree. Two small additions:
1. Parametrize/copy the two thumbnail tests in `test_models.py` for `markdown_file` (delete + replace).
2. Extend `test_blog_detail_strips_external_img_src` (`test_views.py:622`) markdown with a `camo.githubusercontent.com` and a `github.com/` image and assert both survive.

Effort: S. Risk: none.

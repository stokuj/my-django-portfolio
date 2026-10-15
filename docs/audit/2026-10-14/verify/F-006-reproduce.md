# F-006 (reproduce): bleach 6.2.0 has known sanitizer bypasses and is deprecated upstream

**Verdict:** REFUTED as a high-severity security gap (facts partly true, impact not reproducible)
**Confidence:** high
**Adjusted severity:** low (category: library)

## What holds
- `pyproject.toml:8` pins `bleach==6.2.0`; installed version is 6.2.0.
- `_render_markdown_to_html` (`django/main/views.py:357-377`) is the only sanitizer; output is rendered with `|safe` in `django/main/templates/projects/detail.html:18`.
- PyPI advisory data for bleach 6.2.0 lists GHSA-gj48-438w-jh9v and GHSA-8rfp-98v4-mmr6, both fixed in 6.4.0 (latest release).

## Why neither advisory is an exploitable path here
- **GHSA-gj48-438w-jh9v** (`formaction` not URI-sanitized): requires `button`/`input` tags with `formaction` allowed. Allowlist at `django/main/views.py:62-67` permits only `a[href,title]`, `div[class]`, `img[src,alt,title]`, `span[class]`; `button`/`input`/`form` are not in `ALLOWED_MARKDOWN_TAGS`. Not reachable.
- **GHSA-8rfp-98v4-mmr6** (`javascript​:` passes through in `a[href]`): config matches (`a` + `href` allowed), but the advisory itself states browsers do not execute such URIs (invalid scheme per RFC 3986) and "this is not a direct XSS vulnerability". It is a contract violation only, exploitable only if something downstream strips invisible chars before rendering; nothing here does.
- `img[src]` is additionally restricted to GitHub prefixes by `_clean_attributes` (`django/main/views.py:77-87`).
- Input source is README markdown fetched from admin-configured GitHub repos (`django/main/markdown_sync.py:68-90`), loaded via `_load_project_markdown` (`views.py:340`); not anonymous user input.

## Better proposal
Bump `bleach==6.4.0` as routine dependency hygiene (S, low). Defer the nh3 migration; it is not justified by a reachable vulnerability. Adding a regression test for `javascript:` / zero-width-scheme hrefs in `_render_markdown_to_html` is cheap and worth doing with the bump.

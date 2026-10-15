# F-006 (worth lens): bleach 6.2.0 has known sanitizer bypasses and is deprecated upstream

**Verdict:** CONFIRMED with lower severity (the bump is worth doing; "high" is overstated)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `pyproject.toml:8` pins `bleach==6.2.0`. `django/main/views.py:371-377` calls `bleach.clean` and `projects/detail.html:18` renders the output with `|safe`. These facts are correct.
- Both advisories are real. OSV lists GHSA-8rfp-98v4-mmr6 and GHSA-gj48-438w-jh9v as affecting all versions below 6.4.0. PyPI's latest release is 6.4.0, which requires Python >=3.10, so it fits the project's `requires-python >=3.13,<3.14` (`pyproject.toml:5`).
- **GHSA-gj48 does not apply here.** It affects the `formaction` attribute. The attribute allowlist (`views.py:62-67`) and `_clean_attributes` (`views.py:77-87`) allow only `href`, `title`, `class`, `src` and `alt`. There is no `formaction` and no button, input or form tag.
- **GHSA-8rfp applies, but its impact is limited.** The config does allow `a[href]` (`views.py:63`). The advisory itself says it is "not a direct XSS vulnerability": browsers do not run `javascript​:` as a scheme. It only breaks bleach's promise that disallowed schemes are removed.
- **Input trust is high.** The markdown is the owner's own GitHub README. Admins set `github_url` (`markdown_sync.py:68-76`), and the fetch goes to raw.githubusercontent.com. An attacker would need write access to the owner's repos. This is not anonymous input.
- **The nh3 migration is not justified now.** Bleach is deprecated but still gets security fixes, and 6.4.0 shipped them. Moving to nh3 would rewrite the sanitizer (callable attribute filter, different output) to gain nothing beyond the bump. YAGNI applies until bleach stops shipping fixes.

## Better proposal
1. Change `pyproject.toml:8` to `bleach==6.4.0` and run `uv lock`. This takes one line plus the lockfile and is effort S.
2. Optionally add one regression test. Assert that `_render_markdown_to_html('[x](javascript​:alert(1))')` produces no `href` containing `javascript`.
3. Leave the nh3 migration out. Revisit it only if bleach stops shipping security releases.

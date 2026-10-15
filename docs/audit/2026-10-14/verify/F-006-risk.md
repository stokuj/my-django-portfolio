# F-006 (risk lens): bleach 6.2.0 has known sanitizer bypasses and is deprecated upstream

**Verdict:** PARTIALLY REFUTED. The facts are correct, the severity is not, and only the bump half of the proposal is low risk.
**Confidence:** high
**Adjusted severity:** low (category: library)

## Facts confirmed
- `pyproject.toml:8` pins `bleach==6.2.0`, and 6.2.0 is installed in `.venv`.
- `django/main/views.py:371-377`: `bleach.clean(tags=..., attributes=_clean_attributes, protocols=[http, https, mailto], strip=True)`.
- The output is rendered with `|safe` at `django/main/templates/projects/detail.html:18`.

## Why "high" is overstated
- **GHSA-gj48-438w-jh9v** needs `formaction` on `button`/`input`. Neither the tags (`views.py:33-61`) nor the attribute is allowed. `_clean_attributes` rejects every attribute not on the allowlist (`views.py:77-87`). Not reachable.
- **GHSA-8rfp-98v4-mmr6** can formally be reached through `a[href]` (`views.py:63`). The advisory itself says it is not a direct XSS: it only matters when a later step normalizes Unicode, and this app has no such step.
- **Input is semi-trusted.** It is the README of a repo the admin configured, or an admin-uploaded file. No anonymous user can supply it.

## Risks of applying the fix
1. **Bump to 6.4.0: low risk.**
   - `clean()` keeps the same signature, so the callable `attributes=` and `strip=True` keep working.
   - Python 3.13 (`pyproject.toml:5`) meets 6.4.0's minimum of 3.10.
   - Existing tests already guard the behaviour:
     - script stripping: `django/main/tests/test_views.py:396`
     - `onerror` and img-src filtering: `:416` and `:613`
     - safe elements and math output: `:438` onward
   - Needs `uv lock` and `make verify`. The only expected change is the lockfile.
2. **Move to nh3: real regression risk, not justified now.**
   - nh3's `attribute_filter` works differently from bleach's callable. It runs only for attributes that are already allowed, and returns a value or None rather than True or False. The img-src GitHub-only rule (`views.py:84-85`) would need rewriting, and it is easy to get it wrong in a way that lets images through.
   - nh3 adds `rel="noopener noreferrer"` to links by default, and its default handling of relative URLs differs from bleach's. Rendered HTML would change.
   - `class` on `div`/`span` (`views.py:64,66`) carries the arithmatex math markup. nh3 handles classes differently, which could break math rendering (the test at `test_views.py:~470` would catch it).
   - The proposal gates this on tests from F-042. Tests for the core cases already exist. What is missing is a `javascript:` href test, which would be worth adding before any sanitizer swap.

## Better proposal
- Bump `bleach==6.2.0` to `6.4.0`, run `uv lock`, then `make verify`. Effort S. Treat it as library hygiene, not a high-severity security fix.
- Optionally add one test asserting that `[x](javascript:alert(1))` renders with no `javascript:` href.
- Drop the nh3 migration from this finding. Revisit it only if bleach stops shipping security fixes.

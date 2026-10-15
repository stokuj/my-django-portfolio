# F-090: Unrestricted class on div/span allows page-overlay UI redressing

- Lens: reproduce
- Verdict: CONFIRMED (mechanism). The visual impact is overstated.
- Confidence: high
- Adjusted severity: low

## Reasoning
- `django/main/views.py:62-67`: `ALLOWED_MARKDOWN_ATTRIBUTES` allows `class` on `div` and `span`.
- `django/main/views.py:77-87`: `_clean_attributes` adds an extra check only for `img src`. It returns True for every allowlisted attribute, so any `class` value passes.
- `django/main/views.py:357-377`: raw HTML in a README goes through Python-Markdown and then `bleach.clean`. A `div` or `span` keeps whatever classes it had.
- `django/main/templates/projects/detail.html:18`: the result is rendered with `|safe`, so the classes reach the DOM.
- Reachability: READMEs are fetched only from repos that a staff user configured (`markdown_sync.py:68-96`, using `project.github_url` or the profile owner's GitHub). An attacker needs push access to one of those repos, which means the site owner, a collaborator or a compromised account. This is not something an anonymous visitor can do.
- Overstated impact: Tailwind v4 builds only the classes it finds in `templates/**/*.html` and `../**/*.js` (`static/src/css/input.css:2-3`). Of the example payload `fixed inset-0 z-50 bg-black`, only `fixed` and `z-50` exist in the templates (`base.html:14`, `projects/detail.html:38`). `inset-0` and `bg-black` are not generated, so that exact payload does not cover the page. An overlay is still possible with classes that do exist in the build: `fixed`, `z-50`, `top-1/2`, `left-4`, `w-full`, `min-h-screen`, `bg-base-100`, and the daisyUI component classes in use.

## Better proposal
The proposal in the finding is right and needs only a small change in `_clean_attributes`:
```python
if name == "class":
    return value == "arithmatex"
```
Arithmatex in generic mode emits exactly `class="arithmatex"` on `span` and `div`. Effort: S. Add one test to `main/tests` that a `div` with an overlay class has its class stripped.

# F-027 (worth): MathJax typesets sanitized text without ui/safe (\href{javascript:})

**Verdict:** CONFIRMED (fix worth doing, severity overstated)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/static/js/mathjax-config.js:1-23` has no `loader` key, so `ui/safe` is not loaded. MathJax docs (options/safe, web/components/misc) say it must be added via `loader: {load: ['ui/safe']}` and that it exists to stop `\href{javascript:...}`.
- `django/main/views.py:357-377` renders with `pymdownx.arithmatex` (generic) and then `bleach.clean`. Bleach keeps `span`/`div` with `class` (`views.py:62-67`), and the TeX text inside is plain text, so `\href{javascript:...}` gets through. The protocol allowlist at `views.py:68` applies only to real `<a href>` attributes, not to TeX source.
- `templates/projects/detail.html:51-52` loads the config plus `mathjax@3/es5/tex-mml-chtml.js`. In MathJax 3, `\href` is in the base TeX package, and CHTML output turns it into a clickable `<a href>`.
- No CSP was found in `django/config` or `infra`.
- Why the severity is lower: the markdown comes only from READMEs of repos the admin sets up (`markdown_sync.py:68-96`, `Project.github_url`) or from an admin upload. To exploit this, someone needs write access to the owner's repo, and a visitor still has to click the link. So this is defense in depth, not something an anonymous visitor can trigger. It is still worth doing: commit 512ceef ("markdown & URL validation") shows the project treats markdown as untrusted, and this is the one gap left after bleach.
- Risk check: `test_views.py:487-493` only checks that the script URLs are present. Nothing else on the detail page needs MathJax outside the arithmatex output.

## Better proposal (smallest diff)
The security fix is one line: add `loader: {load: ['ui/safe']},` to `mathjax-config.js`.
The `ignoreHtmlClass: '.*|'` / `processHtmlClass: 'arithmatex'` part is a separate scoping and performance tweak. It is fine (it is the config pymdownx documents) but optional. Keep it out of the security fix, or label it clearly in the same commit.
Related, but a separate finding: `mathjax@3` is a floating major version in `detail.html:52`. Pin it to an exact version (e.g. `3.2.2`).

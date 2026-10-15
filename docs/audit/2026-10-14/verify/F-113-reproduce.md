# F-113 - About page called the main landing page

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `README.md:67` under `### About page` reads: "The main landing page showing a brief intro ...".
- `django/main/urls.py:5` maps `""` to `views.home`; `django/main/urls.py:6` also maps `home/` to it.
- `django/main/views.py:100-125` `home()` renders `pages/home.html`.
- About is `django/main/urls.py:7` (`about/` -> `views.about`, rendering `pages/about.html` at `django/main/views.py:143`).
- README itself already describes the real landing page under `### Home page` (`README.md:58-59`), so the About caption contradicts it.

## Better proposal
Same fix, change `README.md:67` to start "Shows a brief intro ..." (drop "The main landing page"). Effort S, no risk.

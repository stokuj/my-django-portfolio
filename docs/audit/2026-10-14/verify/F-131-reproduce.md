# F-131 — Frontend diagram misses edges and templates (reproduce)

**Verdict:** CONFIRMED (mostly; one sub-claim weak)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `errors/404.html:7` and `errors/500.html:7` include `components/hero_section.html`. Diagram has `Errors --> Base` (docs/frontend.md:48) but no `Errors --> Hero` edge (only Home/About/ProjectsIndex at :57,:61,:63). Confirmed.
- `projects/detail.html:28,45` include `projects/components/blog_sidebar_cards.html`; the node `blog_*_sidebar.html` (docs/frontend.md:42) matches only `blog_projects_sidebar.html` (detail.html:27,40). Confirmed.
- `components/hero_section.html:4` does `{% include hero_content_template %}`; the 5 files in `components/hero/*_content.html` are not in the diagram. Confirmed.
- `static/js/mathjax-config.js` (detail.html:51): partly covered by the existing node `MathJax["MathJax scripts (detail page)"]` (docs/frontend.md:28, edge :71). Not a real omission, only a naming detail.

## Better proposal
Add `Errors --> Hero`, rename node at :42 to list `blog_projects_sidebar.html` + `blog_sidebar_cards.html`, add `HeroContent["components/hero/*_content.html"]` with `Hero --> HeroContent`. Optionally relabel the MathJax node to mention `mathjax-config.js` + CDN; not required.

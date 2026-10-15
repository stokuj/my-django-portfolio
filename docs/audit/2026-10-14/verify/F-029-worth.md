# F-029 (worth lens): Unlayered h1/h2/h3 rules override all Tailwind font sizes

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (visual bug, not security or data)

## Reasoning
- `django/main/static/src/css/input.css:9-17` defines `h1/h2/h3 { @apply text-* }` outside any `@layer`. A test build (Tailwind v4.1, to /tmp) puts them unlayered at the top level (line ~3259 of the output), while utilities sit in `@layer utilities`.
- CSS cascade layers: normal unlayered declarations beat every layered one, whatever the specificity or source order. The finding's "come after" wording is wrong about the reason, but the effect is right.
- Affected markup:
  - `templates/components/hero/error_404_content.html:3`, `error_500_content.html:3`: `text-4xl sm:text-5xl` -> sm:5xl never applies.
  - `hero/about_content.html:2` (`text-3xl sm:text-4xl`), `hero/projects_content.html:1` (`text-2xl sm:text-3xl`) -> always 4xl.
  - `pages/home.html:10`, `base.html:119` (`h2 text-2xl`) -> rendered at xl.
  - `.md-article h1/h2/h3` in `@layer components` (`input.css:52-62`) -> overridden by the bare h1/h2/h3 rules.
- Nothing in the git log or docs/ says this was intentional (the rules date back to early commits `1d2597c`/`b439a83`).

## Proposal check
Wrapping lines 9-17 in `@layer base { ... }` is the smallest correct fix and is the standard Tailwind v4 pattern. The user rule is appended after preflight in `base`, so it still beats preflight's `font-size: inherit` and stays the default for headings with no size class. Components and utilities then override it as intended.
Risk: the projects hero h1 shrinks from 4xl to 2xl/3xl, and markdown headings change size. This is the intended look, but check it visually.

## Better proposal
None. Optional: also move `html { scrollbar-gutter }` (input.css:19-21) into the same `@layer base` for consistency. It is not required.

# F-029 (reproduce lens): Unlayered h1/h2/h3 rules override all Tailwind font sizes

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (visual bug only; no functional or security impact)

## Reasoning
- `django/main/static/src/css/input.css:9-17` defines `h1 { @apply text-4xl }`, `h2 { @apply text-xl }`, `h3 { @apply text-lg }` outside any `@layer`. Tailwind is v4 (`package.json`: `tailwindcss ^4.1.4`), which emits native CSS cascade layers.
- I built the CSS into `/tmp/f029.css` with the repo's `node_modules/.bin/tailwindcss`, without touching the repo's `style.css`. The output has `@layer theme, base, components, utilities;` at line 3 and utilities in `@layer utilities` (lines 195+, e.g. `.text-2xl` at 2858 and `.sm\:text-4xl` at 3174). The heading rules come out unlayered at lines 3259-3267. `.md-article h1/h2` are in `@layer components` at lines 3397/3405.
- In the CSS cascade, normal unlayered declarations beat normal declarations in any layer, whatever their specificity or source order. The finding's "come after utilities" wording is incidental: the rules would win even if they came first.
- Affected templates (rendered size vs intended size):
  - `components/hero/projects_content.html:1`: h1 `text-2xl sm:text-3xl` renders at 4xl.
  - `components/hero/about_content.html:2`: h1 `text-3xl sm:text-4xl` is always 4xl.
  - `components/hero/error_404_content.html:3` and `error_500_content.html:3`: `sm:text-5xl` never applies.
  - `base.html:119` and `pages/home.html:10`: h2 `text-2xl` renders at xl.
  - `components/timeline_project_item.html:3`: h3 `text-base` renders at lg.
  - `projects/components/project_card.html:34` (h2 `text-lg`) and `blog_sidebar_cards.html:4,17` (h2 `text-base`) render at xl.
  - `.md-article h1/h2/h3` (`input.css:52-62`, used at `projects/detail.html:18`) render at 4xl/xl/lg instead of 3xl/2xl/xl.

## Proposal
The finding's proposal is correct: wrap lines 9-17 in `@layer base { ... }`. Unclassed headings (e.g. `home_content.html:2`) keep the 4xl/xl/lg defaults, because the base rules still come after preflight within the base layer. Check the hero and blog pages visually afterwards, since headings that look "right" today will change size.

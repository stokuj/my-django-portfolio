# F-081 - Dead CSS classes (hover:bg-primary-focus, menu-compact, prose)

**Verdict:** PARTIALLY CONFIRMED (not refuted; `prose` part is wrong)
**Confidence:** high
**Adjusted severity:** low

## Method
Built CSS from `django/main/static/src/css/input.css` with the repo's Tailwind 4 + daisyUI 5 setup (`npx @tailwindcss/cli`) into a temp file outside the repo and grepped the output.

## Reasoning
- `hover:bg-primary-focus` (`django/main/templates/base.html:165`): 0 matches in built CSS. daisyUI 5 has no `primary-focus` color; custom themes (`input.css:105-160`) define only `--color-primary`/`--color-primary-content`. Dead. CONFIRMED.
- `menu-compact` (`base.html:42`): 0 matches. Not a daisyUI 5 class. Dead. CONFIRMED.
- `not-prose` (`django/main/templates/projects/detail.html:26`): 0 matches. Dead. CONFIRMED.
- `prose` (`detail.html:9`): NOT dead. Without `@tailwindcss/typography`, daisyUI 5 still emits a `.prose` rule: `:root .prose :where(code):not(pre > code) { background-color; border-radius: var(--radius-selector); border: var(--border) solid var(--color-base-300); padding-inline: 0.5em; }` plus `.prose .btn { text-decoration-line: none }`. It sits in the utilities layer, so it overrides `.md-article code` (`input.css:84-86`, components layer). Removing `prose` drops the border/padding on inline code in rendered READMEs. REFUTED for this part; "Risk: None" is wrong.

## Better proposal
Delete `hover:bg-primary-focus`, `menu-compact` and `not-prose`. Keep `prose`, or drop it only after a visual check of inline `code` in a project README (and move the border into `.md-article code` if wanted). Effort S.

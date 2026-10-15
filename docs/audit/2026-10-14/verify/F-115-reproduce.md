# F-115 — make verify prerequisites omit npm install (reproduce lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `README.md:143`: "`make verify` expects the dev dependencies installed through `uv sync --extra dev`." No mention of npm.
- `Makefile:34`: first step of `verify` is `npm run build:css:prod`.
- `package.json:4`: that script runs `npx @tailwindcss/cli ...`; `@tailwindcss/cli`, `tailwindcss`, `daisyui` are devDependencies (`package.json:8-10`).
- `django/main/static/src/css/input.css:1,5`: `@import "tailwindcss"` and `@plugin "daisyui"` need both packages resolvable from `node_modules`.
- CI does `npm ci` (`.github/workflows/django.yml:37`) before `make verify` (`:46`), confirming npm deps are a real prerequisite.

## Mitigation (why it stays low)
- The README's local setup block already runs `npm install` (`README.md:115-117`) and lists Node.js + npm as prerequisites (`README.md:109`). Anyone who followed the README top to bottom already has `node_modules`. The gap only bites a reader who jumps straight to "Verification Commands".

## Better proposal
Same as proposed, one-line edit at `README.md:143`:
"`make verify` expects `uv sync --extra dev` and `npm install` (it builds CSS first)."
Effort S, risk none.

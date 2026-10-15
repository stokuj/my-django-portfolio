# F-105 - Unused @catppuccin/daisyui devDependency

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `package.json:12-14` declares `"@catppuccin/daisyui": "^2.1.1"` under devDependencies.
- Repo-wide search (excluding node_modules, lockfiles, built CSS, audit docs) finds `catppuccin` only at `package.json:13`.
- `django/main/static/src/css/input.css:5-7` loads `@plugin "daisyui"` with themes `dim2, fantasy3`; both are custom themes defined locally via `@plugin "daisyui/theme"` at `input.css:105-106` (fantasy3) and `input.css:141-142` (dim2). No Catppuccin theme (latte/frappe/macchiato/mocha) or import is used.
- Build paths (`Makefile:34`, `infra/Dockerfile:4-7`, `.github/workflows/docker-build-push.yml:42-43`, `.github/workflows/django.yml:37`) run `npm ci` + `build:css:prod`, which only invokes the Tailwind CLI on `input.css`; nothing pulls in the package.
- `npm ci` installs devDependencies by default, so the package is downloaded in CI and the Docker build stage for no effect.

## Proposal
Agree: `npm uninstall @catppuccin/daisyui` (updates package-lock.json too), then `npm run build:css:prod` to confirm the CSS still builds. Effort S, no runtime risk.

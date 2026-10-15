# F-082 — Heavy hero PNGs under an overlay; one image unused

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/templates/components/hero_section.html:2` sets `background-image: url('{% static hero_background %}')`, with an overlay div at line 3 (default `bg-base-100/85`).
- Callers:
  - `django/main/templates/pages/home.html:6` uses `images/hero-bg.png` under `bg-base-100/85`.
  - `pages/about.html:7`, `projects/index.html:6`, `errors/404.html:7`, `errors/500.html:7` use `images/hero-bg2.png` under `/85` or `/90`.
- File sizes at HEAD: `hero-bg.png` 3,039,059 B (1536x1024), `hero-bg2.png` 1,300,759 B (1024x1024), `hero-bg3.png` 1,553,964 B (1024x1024).
- `git grep hero-bg3` finds no reference outside `docs/audit`, and the compiled CSS does not mention it either. The image is unused.
- Nothing in the infra/Caddy config references these images, so no build step produces optimized copies.

## Correction to the proposal
- Resizing "to about 1600px wide" does nothing, because the images are already 1536px and 1024px wide. The saving comes only from re-encoding.

## Better proposal
- Delete `django/main/static/images/hero-bg3.png`.
- Re-encode `hero-bg.png` and `hero-bg2.png` to WebP (quality ~70; a 85-90% overlay hides artifacts). Update the 5 `hero_background=` arguments to point at the new files. Effort S.

# F-052 — Pillow 12.2.0 has advisories fixed in 12.3.0 (worth lens)

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low (was medium)

## Reasoning
- `pyproject.toml:15` pins `pillow==12.2.0`. PyPI JSON for 12.2.0 lists 25 records (13 unique CVEs), all with `fixed_in: 12.3.0`. 12.3.0 was released 2026-07-01. The advisory count in the finding is correct.
- The prod image installs from the pyproject pins, not the lock: `infra/Dockerfile:27` runs `uv pip install --system .`. CI uses the lock: `.github/workflows/django.yml:34` runs `uv sync`. So both files need the bump, or the two get out of step.
- There is a precedent for this kind of change: `ec37bac` ("patch Dependabot vulnerabilities — pillow, ...") bumped Pillow the same way. No doc or commit says to stay on 12.2.x.
- Real exposure is narrow. Pillow is used only through Django's `ImageField` (`django/main/models.py:59`). Nothing in `django/main` imports PIL directly, and there is no `request.FILES` path, so only admins can upload. Most of the CVEs are in code this app never runs: font loaders (PCF/BDF/FontFile), GD, WindowsViewer, ImageCms, the TGA/PDF encoders and rank filters. What a crafted upload could actually reach is the format parsers that Django's `Image.open` + `verify()` calls (EPS header, raw tile, JPEG2000). That still needs a malicious or compromised admin. This makes it low rather than medium, but the fix is cheap enough that it is still worth doing.

## Better proposal
Same bump, but keep the lock in sync: edit `pyproject.toml:15` to `pillow==12.3.0`, then run `uv lock --upgrade-package pillow` and commit both files. Then run `make verify`. Effort S, risk low (minor release, no API used beyond ImageField validation).

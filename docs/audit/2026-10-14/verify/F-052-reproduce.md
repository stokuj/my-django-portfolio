# F-052: Pillow 12.2.0 has advisories fixed in 12.3.0 (reproduce lens)

**Verdict:** CONFIRMED (facts). The severity is overstated.
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `pyproject.toml:15` pins `pillow==12.2.0`. The local `.venv` also has 12.2.0 installed.
- PyPI lists 12.3.0 as the latest release. OSV (api.osv.dev, queried 2026-10-15) returns 13 unique GHSAs for pillow 12.2.0, and every one is fixed in 12.3.0. The count of 13 is correct, and the named issues are real:
  - GHSA-6r8x-57c9-28j4 (heap OOB write in paste/crop)
  - several `_decompression_bomb_check` bypasses (BDF, PCF and Gd fonts, PdfStream)
- Reachability is narrow:
  - The only Pillow entry point is `Project.thumbnail = models.ImageField(...)` (`django/main/models.py:59`).
  - The code never imports `PIL` directly (grep over `django/` finds nothing), and there are no custom upload forms or views for images.
  - Pillow is therefore reached only through Django's ImageField form validation (`Image.open` + `verify`), when a staff user uploads a file in the admin.
  - The paste/crop OOB write, the RankFilter and ImageCms bugs, the font-loader bypasses, the TGA encoder and the WindowsViewer issues are never called. Only header-parse or decode DoS bugs (JPEG2000, EPS, McIdas) are theoretically reachable, and an attacker would already need admin access.
- The finding admits the path is admin-only, which contradicts "medium". Severity by the rubric is "low" (hygiene bump).

## Better proposal
Bump to `pillow==12.3.0` (S effort, low risk) during the next routine dependency update, and regenerate `uv.lock`. Drop the claim that the paste/crop OOB write is reachable.

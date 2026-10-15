# F-084 (reproduce): Heatmap inline JS over-generalised (one-element variants, dead tooltip mode)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged); effort S-M

## Reasoning (HEAD, branch dev)
- Inline script spans `django/main/templates/pages/about.html:258-464` (~206 lines), as claimed.
- `variantConfigs` has a single entry (`about.html:260-266`, prefix `heatmap-minimal`); the `.map().filter()` over 9 element lookups (`about.html:268-293`) and the `if (!variants.length)` guard (`:295`) only serve that one variant. Every later step loops `variants.forEach` over one item.
- `tooltipMode` is hard-coded `"title"` (`:264`); the `"daisy"` branch (`:422-424`) can never run.
- `day.contribution_count` fallback (`:400`) is dead: the payload comes from `build_weeks_payload`, which only writes `count` and `level` (`django/main/heatmap.py:50-57`), and `about_heatmap_data` returns that as `raw` (`django/main/views.py:171-186`). The same dead fallback exists server-side in `views.py:231`.
- Colour thresholds differ: JS `contributionColor` (`about.html:315-321`) gives `<3,<6,<9,else`, server `contribution_level` (`heatmap.py:19-29`) gives `<=2,<=5,<=9,else`. Count 9 renders the darkest colour (`#216e39`, level 4) in JS while the server says level 3. The server `level` field is sent but never used by the JS.
- CSP point is weak: no CSP is configured anywhere (no `CSP`/`Content-Security-Policy` in `django/config` or `django/main`), so nothing is blocked today. It is a future-only concern, not a current defect.

## Better proposal (smaller)
Keep the script inline (no CSP exists, so moving it to `static/js/heatmap.js` with data-* is optional churn). In place:
1. Replace `variantConfigs`/`variants` with direct `const statusEl = document.getElementById("heatmap-minimal-status")` etc.; drop the `forEach` wrappers.
2. Delete the `daisy` branch and the `contribution_count` fallback (also in `views.py:231`).
3. Replace `contributionColor` with `const COLORS = ["", "#9be9a8", "#40c463", "#30a14e", "#216e39"]; COLORS[day.level || 0]` so the server owns the thresholds (fixes the count=9 mismatch).
4. Optional: render the "disabled" message with `{% if not heatmap_enabled %}` in the template instead of `heatmapEnabled` JS.
Check visually on /about after the change.

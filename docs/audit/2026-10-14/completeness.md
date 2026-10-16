# Completeness review (2026-10-14 audit)

`find/` and `verify/` were deleted after Phase 12 (Q21); they are in git history up to commit `c664fdf`.

Scope: `git ls-files` at HEAD (dev), minus lockfiles, migrations, images and built CSS, compared against the 107 merged findings and the 20 lens reports in `find/`.

## Assessment

Coverage is good for the core: views, models, tasks, integrations, settings, CI/CD, Docker/compose/Caddy, dependencies, tests and the main templates/JS. All 20 lenses produced reports. No lens failed.

Files that no finding cites, or that a lens only mentioned in passing:

| Area | Files | Status |
|------|-------|--------|
| Django admin | `django/main/admin.py` (116 lines), `django/config/urls.py:24` | Mentioned only as duplication in F-072. Nobody reviewed the admin as an attack surface or for usability. |
| SEO / document head | `django/main/templates/base.html:5-9` | No lens covered it. The head has no meta description, Open Graph tags, canonical link or favicon, and there is no robots.txt or sitemap route. |
| Secondary templates | `errors/404.html`, `errors/500.html`, `components/hero/*_content.html`, `components/timeline_project_item.html`, `projects/components/blog_sidebar_cards.html`, `projects/components/blog_projects_sidebar.html`, `components/icons/*` | No finding cites them. |
| Human-facing docs | `README.md`, `docs/architecture.md`, `docs/frontend.md`, `.env.example`, `.github/ISSUE_TEMPLATE/*` | F-019, F-043 and F-098 cover CLAUDE.md, docs/superpowers and docs/implementation.md only. README and the architecture and frontend docs were not checked against the code. |
| Misc | `django/config/celery.py`, `asgi.py`, `wsgi.py`, `apps.py`, `manage.py`, `.gitattributes`, `.dockerignore`, `LICENSE` | These are trivial, or a lens checked them and found nothing (the Dockerfile copies only `django/`, so `.dockerignore` gaps do not matter). No gap. |

`django/main/validators.py` was checked by devkit-integrations, which found no defect (`find/06-devkit-integrations.md:73`).

Verify pipeline: only F-001..F-011 have `-risk` files and only F-001..F-053 have `-worth` files. This looks like severity-based triage and not a failed lens. It is listed here only so the orchestrator can confirm it.

## Gaps

1. **admin-surface**: Django admin security and usability (default `/admin/` path, no login throttling, raw `PageView`/`Tag` registration, upload fields).
2. **seo-head**: missing SEO and social metadata, robots.txt, sitemap and favicon.
3. **secondary-templates**: correctness and accessibility pass over the uncited templates (error pages, hero contents, timeline item, blog sidebars).
4. **human-docs-drift**: README.md, docs/architecture.md, docs/frontend.md, .env.example and the issue templates checked against the code at HEAD.

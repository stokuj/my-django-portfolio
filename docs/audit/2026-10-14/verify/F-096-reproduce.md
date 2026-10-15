# F-096 — Blog markdown re-read and re-rendered on every request

**Lens:** reproduce
**Verdict:** CONFIRMED (factually), impact negligible
**Confidence:** high
**Adjusted severity:** low

## Reasoning

- `django/main/views.py:399-418` `blog_detail` calls `_load_project_markdown(project)` (`views.py:340-354`, opens and reads the FileField) and `_render_markdown_to_html` (`views.py:357-377`, `markdown.markdown` + `bleach.clean`) on every request. No caching anywhere in the view.
- Sidebar query `Project.objects.order_by("-date")` is at `views.py:405` (finding says 406). It loads every column, including `tech_stack`/`tools_libraries` JSONFields (`models.py:66-67`). The template `projects/components/blog_projects_sidebar.html` only uses `id`, `title`, `blog`, `blog_url`, `github_url`.
- No `CACHES` setting in `django/config/settings.py`, so `cache.get_or_set` would fall back to per-process LocMemCache (works, but per Gunicorn worker; Redis is available if a shared cache is wanted).

## Why impact is minimal

Personal portfolio: a handful of projects, small README files, low traffic. Markdown+bleach on a few KB costs milliseconds; the sidebar query returns a few rows. This is a micro-optimisation, not a measurable problem. Adding a cache also adds an invalidation concern (sync task rewrites files every 2h; F-003 fixed filename makes name-based keys stale).

## Better proposal

- Sidebar: `Project.objects.only("id", "title", "blog", "blog_url", "github_url", "date").order_by("-date")` — one line, zero risk. Worth doing.
- Rendered HTML cache: skip unless profiling shows a cost. If done, key on `project.pk` + file mtime/size (or content hash) so syncs invalidate it automatically.

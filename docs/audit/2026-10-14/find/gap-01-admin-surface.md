# gap-admin-surface

Scope: Django admin as attack surface and for usability at HEAD (admin.py, config/urls.py, settings.py upload/cookie settings, models.py upload fields, infra/Caddyfile). Skipped: F-024, F-025, F-026, F-044 (nosniff / sniffing of /media), F-072, F-078; F-009 (1 Gunicorn worker) referenced only.

Verified OK: CSRF and session cookies are `Secure` in prod (settings.py:99-100), HttpOnly session cookie by Django default; SVG/HTML thumbnails are rejected because `ImageField` validates by Pillow and image-extension (models.py:59); password validators are on (settings.py:125-138).

## 1. No brute-force or rate-limit protection on /admin/login/
- Severity: medium
- Category: security
- File: django/config/urls.py:24
- Problem: admin is on the default `admin/` path; no lockout app in deps (pyproject.toml:7-22: no django-axes or similar), no `AUTHENTICATION_BACKENDS` throttle (settings.py:168-170), and Caddy proxies everything except /static and /media straight to Django with no path restriction or rate limit (infra/Caddyfile:16-29, stock `caddy:2` image has no rate-limit module). Unlimited password guesses are possible. Each failed login runs a full PBKDF2 hash, so login spam is also a cheap CPU DoS against the single sync worker (F-009).
- Proposal: add `django-axes` (lockout per username+IP, few lines in settings) or, with zero deps, restrict `/admin*` in Caddy (`@admin path /admin*` + `remote_ip` allowlist or `basic_auth`). Optionally move admin to a non-default path via env.
- Effort: S
- Risk: Caddy allowlist locks the owner out from new IPs; axes needs `AXES_*` config and one migration.

## 2. No request-body size limit for file uploads; settings comment is wrong
- Severity: medium
- Category: security
- File: django/config/settings.py:179
- Problem: `DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB limit for file uploads` does not apply to file parts of multipart bodies (Django excludes upload data from that check). There is no `FILE_UPLOAD_*` cap, no model/form size validator on `thumbnail` or `markdown_file` (models.py:59-65), and no `request_body max_size` in Caddy (infra/Caddyfile:16-29). Any POST with a multipart body (even unauthenticated, since `CsrfViewMiddleware` reads `request.POST` once a csrftoken cookie and same-origin Referer are supplied) is streamed to temp disk with no upper bound, while holding the single worker.
- Proposal: add `request_body { max_size 10MB }` to the app site block in the Caddyfile; fix the comment; add a small size validator (e.g. 2 MB) on `thumbnail` and `markdown_file`.
- Effort: S
- Risk: legit thumbnails above the chosen cap get rejected; pick the cap above current largest file.

## 3. Admin .md upload is validated only by extension and is silently overwritten by sync
- Severity: low
- Category: bug
- File: django/main/models.py:60
- Problem: the GitHub sync path enforces a size limit, UTF-8 decode and rejects HTML (markdown_sync.py:112-132). The admin upload path checks only the `.md` extension (models.py:62). A non-UTF-8 file uploads fine and then renders as an empty blog page (`_load_project_markdown` returns None on `UnicodeDecodeError`, views.py:346-349). For `blog=True` projects the 2-hourly sync replaces the uploaded file with the GitHub README (tasks.py:36, markdown_sync.py:168-172) and the admin form does not say so.
- Proposal: add a small validator (size cap + `decode("utf-8")`) on `markdown_file` reusing `MAX_MARKDOWN_SIZE_BYTES`; add `help_text` that the file is replaced by sync when `blog` is on.
- Effort: S
- Risk: needs a migration (validators/help_text are no-op migrations).

## 4. TaskExecutionStatus/Log admins allow add and delete of read-only system rows
- Severity: low
- Category: security
- File: django/main/admin.py:63
- Problem: every field is in `readonly_fields` (admin.py:75-85, 100-111) but `has_add_permission`/`has_delete_permission` are not overridden. Staff can "add" a blank row (TaskExecutionStatus with `task_name=""`; a second add hits the unique constraint on `task_name`, models.py:130) and can delete log history or the status snapshot shown on the about page. The change view also shows a useless Save button.
- Proposal: in both admins return `False` from `has_add_permission` and `has_change_permission` (keep view), and `False` from `has_delete_permission` on the log admin (or keep delete only for superusers if manual pruning is wanted).
- Effort: S
- Risk: none; tasks write via ORM, not admin.

## 5. PageView counter registered raw
- Severity: low
- Category: architecture
- File: django/main/admin.py:116
- Problem: `admin.site.register(PageView)` exposes add/delete/edit of the singleton counter. Added rows (id != 1) are never read (context_processors.py:15, middleware.py:15-16); deleting id=1 silently resets the public visitor count.
- Proposal: drop the registration (counter is visible on the site), or register with add/delete disabled and `readonly_fields = ("count",)`.
- Effort: S
- Risk: none.

## 6. ProjectAdmin and TaskExecutionLogAdmin list views are hard to use
- Severity: low
- Category: frontend
- File: django/main/admin.py:14
- Problem: `ProjectAdmin.list_display` shows raw JSON lists `tech_stack`, `tools_libraries` and the file path `markdown_file` (admin.py:19-21), has no `list_filter` (status, blog, tags), no `filter_horizontal` for the `tags` M2M (models.py:79), no ordering (Project has no `Meta.ordering`). `TaskExecutionLogAdmin` (admin.py:89-112) has no `ordering`, `list_filter` on `task_name`/`last_status`, or `date_hierarchy`; TaskExecutionLog has no `Meta.ordering` (models.py:146-166), so oldest runs appear first. `Tag` is registered raw with no search (admin.py:115).
- Proposal: ProjectAdmin: `list_display = ("title", "status", "blog", "blog_url", "date")`, `list_filter = ("status", "blog", "tags")`, `filter_horizontal = ("tags",)`, `ordering = ("-date",)`. TaskExecutionLogAdmin: `ordering = ("-created_at",)`, `list_filter = ("task_name", "last_status")`, `date_hierarchy = "created_at"`.
- Effort: S
- Risk: none.

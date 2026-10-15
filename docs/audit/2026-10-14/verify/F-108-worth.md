# F-108 (worth): No request-body size limit for file uploads; settings comment is wrong

**Verdict:** CONFIRMED (core claim), proposal trimmed
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/config/settings.py:179` sets `DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB limit for file uploads`. Django excludes file parts from this setting, so the comment is wrong. No `FILE_UPLOAD_*` setting exists anywhere in `django/config/`.
- `infra/Caddyfile:16-29` has no `request_body` directive. Caddy sets no default body limit.
- Unauthenticated reachability holds. The middleware order at `settings.py:57-66` puts no custom middleware that reads the body (`main/middleware.py` never touches POST/body). In Django 5.1.15, `CsrfViewMiddleware._check_token` reads `request.POST` once a well-formed `csrftoken` cookie is present. A non-browser client picks that cookie itself and sends a matching `Origin` header. Every resolved URL works, for example `/` (`main/urls.py:5`). The multipart parser then spools file parts above 2.5 MB to container temp disk with no total cap.
- Gunicorn runs with defaults, so one sync worker (`infra/docker-compose.prod.yml:46`).
- Nothing in docs/ or git log shows a deliberate choice against a body limit. The setting comes from an old ckeditor commit (`43f12c6`).

## Why severity drops
- The impact is a transient DoS. Temp files are deleted when the request ends or fails, and filling the disk costs the attacker the same amount of bandwidth.
- The proposed cap does not fix the "holds the single worker" part. Caddy streams request bodies, so a slow 9 MB upload still ties up the only sync worker. That is a gunicorn worker class/count issue and outside this finding.

## Better proposal (smallest diff)
1. In the `https://{$APP_DOMAIN}` block, add `request_body { max_size 10MB }`. This one change covers every endpoint, the admin included.
2. Fix the comment at `settings.py:179`, for example `# max non-file request body held in memory`.
3. Drop the model size validators on `thumbnail`/`markdown_file` (`models.py:59-65`). Only staff can reach those fields through the admin, and the Caddy cap already bounds them. Add a validator only if a product rule on thumbnail size actually exists.

Effort: S.

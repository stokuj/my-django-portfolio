# F-108 (reproduce): No request-body size limit for file uploads; settings comment is wrong

**Verdict:** CONFIRMED (core claim), impact overstated
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/config/settings.py:179` sets `DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB limit for file uploads`. Django excludes file parts from this limit, so the comment is wrong. No `FILE_UPLOAD_*` setting exists anywhere in `django/config` or `infra`.
- `django/main/models.py:59-65`: `thumbnail` has no validator, `markdown_file` has only `FileExtensionValidator`. Neither has a size check.
- `infra/Caddyfile:16-29`: the app block is `reverse_proxy web:8000` with no `request_body { max_size }`, and Caddy has no default body cap.
- Reachable without authentication: `CsrfViewMiddleware` (settings.py:62) runs `process_view` on every resolved URL (e.g. `/`, `/admin/login/`). After the Origin/Referer check, which a non-browser client passes by sending a matching `Origin`, `_check_token` reads `request.POST.get("csrfmiddlewaretoken")` whenever a well-formed `csrftoken` cookie is present. The attacker can supply that cookie. Reading `request.POST` parses the multipart body, and file parts over 2.5 MB are streamed to temp disk with no size limit.
- Single worker: `infra/docker-compose.prod.yml:46` runs `gunicorn config.wsgi:application --bind 0.0.0.0:8000` with no flags, so it uses the defaults: 1 sync worker and `timeout=30`.

## Why severity is lower
- The temp files are removed when the request ends (the 403 or response path closes the uploaded files), so disk fill is temporary and not data loss.
- The Gunicorn 30 s worker timeout bounds each request. Requests are handled one at a time because there is one worker.
- Tying up the single worker is possible with any slow POST body through the non-buffering Caddy proxy, whatever the size. A size cap does not fix that, so it is not a distinct gap of this finding.

## Better proposal
- Add `request_body { max_size 10MB }` to the `https://{$APP_DOMAIN}` block in `infra/Caddyfile` and fix the comment at settings.py:179. Both are S effort and cover the real gap.
- The model size validator is optional. Only admin staff can upload, so it adds little.
- The separate, larger DoS concern is the single sync worker. Consider `--workers 2-3` or a gthread worker. Track that as its own finding.

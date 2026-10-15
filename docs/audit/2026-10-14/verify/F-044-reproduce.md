# F-044 (reproduce lens): Caddy-served /static and /media get no security headers

**Verdict:** CONFIRMED (factually), severity overstated
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `infra/Caddyfile:18-26`: `handle /static/*` and `handle /media/*` run `file_server` with no `header` directive anywhere in the file (1-30). These responses never reach Django, so `SecurityMiddleware` (`django/config/settings.py:58`) does not add headers to them. The claim is correct.
- Prod uses this file: `infra/docker-compose.prod.yml:159` mounts it, and `:161`/`:163` mount the static and media volumes under `/srv`.
- The impact is smaller than the finding says:
  - HSTS is set per host. Django sends it on every HTML response (`settings.py:102-104`), so browsers already apply it to the whole host, including /static and /media. A missing HSTS header on asset responses changes nothing in practice.
  - Uploads come only from admins (`models.py:59-61`). `thumbnail` is an `ImageField`, so Pillow checks the file and it gets an image extension. `markdown_file` only accepts `.md`. Neither field lets someone upload `.html` or `.svg`, and modern browsers do not sniff `image/*` into HTML. There is no reachable XSS path for a non-admin.
  - Referrer-Policy on static assets has close to no privacy value.
- What remains is a defense-in-depth gap, which makes it low, not medium.

## Better proposal
Keep it minimal. Add `header X-Content-Type-Options nosniff` in the site block (or only inside `handle /media/*`). A CSP `sandbox` on /media/* is fine but optional. Leave out HSTS and Referrer-Policy for assets because they are redundant.

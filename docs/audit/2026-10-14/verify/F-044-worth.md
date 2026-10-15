# F-044 — Caddy-served /static and /media get no security headers (worth lens)

**Verdict:** CONFIRMED (gap is real), but overstated — downgrade.
**Confidence:** medium
**Adjusted severity:** low

## Reasoning
- Gap is real: `infra/Caddyfile:18-26` serves /static and /media via `file_server` with no `header` directive, so Django's SecurityMiddleware headers (`settings.py:101-105`, plus Django defaults nosniff / Referrer-Policy same-origin) are absent on those responses.
- HSTS claim is moot: HSTS is a per-host policy; browsers cache it from any Django HTML response (`SECURE_HSTS_SECONDS = 31536000`, `settings.py:102`). Missing it on asset responses changes nothing.
- Referrer-Policy on images/CSS/.md files is near-irrelevant (same-origin subresources, no outbound navigation).
- Only meaningful header is `nosniff` (+ optional CSP sandbox) on /media. Exposure is small: the only upload fields are admin-only (`models.py:59` ImageField validated by Pillow, `models.py:60-64` FileField restricted to `.md`); there is no public upload path (no `request.FILES` usage in `django/main`). Exploitation needs a malicious admin or a compromised GitHub README sync. Defense in depth, not a medium security gap.
- Proposal overreaches: putting `header {...}` in the site block also touches proxied Django responses (duplicates/overrides headers Django already sets), and `-Server` is unrelated scope. Scope it to the file_server handles.

## Better proposal (smallest diff)
Inside the existing handles only:
```
handle /static/* {
    root * /srv
    header X-Content-Type-Options nosniff
    file_server
}
handle /media/* {
    root * /srv
    header {
        X-Content-Type-Options nosniff
        Content-Security-Policy "default-src 'none'; sandbox"
    }
    file_server
}
```
Effort S. Thumbnails are loaded via `<img>` (`project_card.html:11`), so the CSP on the image response itself does not block rendering.

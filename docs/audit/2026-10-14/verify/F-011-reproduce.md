# F-011 — Django 5.1 is EOL with unpatched advisories (reproduce lens)

**Verdict:** CONFIRMED (facts hold), severity overstated
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `pyproject.toml:10` pins `django==5.1.15`. No 5.1.16+ exists on PyPI (last 5.1 release is 5.1.15); 5.2.18 exists, latest is 6.1.2.
- OSV query for django 5.1.15 returns 10 records, including GHSA-h7pc-vwp9-298g (signed-cookie salt collision), GHSA-8qcx-xf44-272x (DomainNameValidator newline), GHSA-3h9f-r86x-qvjx / GHSA-8cjm-8mp7-r2xf / GHSA-923m-gv2p-w5qp (cache middleware leaks), plus GeoDjango/GDAL issues. The EOL + unpatched claim is accurate.
- PG13 constraint is real: `infra/docker-compose.prod.yml:3` and `infra/docker-compose.dev.yml:3` use `postgres:13`; Django 5.2 requires PostgreSQL 14+.

## Reachability (why not high)
- No cache middleware: `django/config/settings.py:57-65` has no `UpdateCacheMiddleware`/`FetchFromCacheMiddleware`; no `CACHES`, `cache_page`, or `cache.` usage in `django/` -> cache-leak advisories not reachable.
- No `DomainNameValidator`, no `django.contrib.gis`/GDAL usage -> those advisories not reachable.
- Signed cookies: only implicit use via `django.contrib.messages` default FallbackStorage (`settings.py:53,64`; `views.py:431-456`). No app code calls `set_signed_cookie`/`get_signed_cookie`/`signing.*`, sessions use default DB backend. Salt collision needs a second attacker-influenced signing namespace, which the app does not have.
- No currently known advisory has a concrete attack path in this app. The real risk is going forward: any future 5.1 issue will never be patched.

## Better proposal
Same bump (django==5.2.18 or a supported 6.x), but sequenced after F-007 (PG 13 -> 14+), so effort is M as a combined change, not S. Classify as medium/ops hygiene, not a high security gap.

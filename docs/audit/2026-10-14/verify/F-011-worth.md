# F-011 - Django 5.1 is EOL with unpatched advisories (worth lens)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** medium (was high)

## Reasoning
- `pyproject.toml:10` pins `django==5.1.15`. Verified.
- OSV query for django 5.1.15 (run 2026-10-15) returns 10 entries published 2026-06 to 2026-10: signed-cookie salt collision (GHSA-h7pc-vwp9-298g), DomainNameValidator newline (GHSA-8qcx-xf44-272x), 3 cache-middleware leaks, plus GeoDjango/GDAL issues. The claim holds.
- PyPI lists 5.2.18 as the latest 5.2 release, so the target version exists. 6.1.2 is the newest overall, but 5.2 LTS is the right target (smallest jump, supported to 2028-04).
- Blocker is real: Django 5.2 needs PostgreSQL >= 14, and prod/dev run `postgres:13` (`infra/docker-compose.prod.yml:3`, `infra/docker-compose.dev.yml:3`). The PG bump was reverted in b8da60e ("migration deferred"). Sequencing after F-007 is correct.
- No conflict with a documented decision: `docs/superpowers/specs/2026-05-14-codebase-audit-design.md:133,168` put 5.2 "out of scope (separate issue)". That defers the upgrade; it does not reject it.

## Why severity drops to medium
Actual exposure at HEAD is low. None of the listed advisories hit a code path this app uses:
- No cache middleware or `cache_page` (`django/config/settings.py:57-66`; grep finds none).
- No GeoDjango/GDAL.
- No `get_signed_cookie`. The only signed-cookie consumer is the messages framework, used only in admin-only views (`django/main/views.py:431-454`).
- No DomainNameValidator. The URLField/EmailField inputs (`django/main/models.py:72,203-205`) are admin-edited only.
Being EOL is the real risk: future advisories will not be patched. That is "should fix", not an exploitable "high".

## Corrections
- Effort: the version bump itself is S, but it is gated on F-007 (PG cutover, M). The finding should state that dependency.
- The "risk: tests don't run in CI until F-002" point is valid. Run `make verify` locally against PG17 before merging, because CI uses SQLite (`django/config/settings.py:111`).

## Better proposal
Same fix, explicitly sequenced: (1) F-007 PG13 -> PG17, (2) a separate PR with `django==5.2.18` in `pyproject.toml:10` plus `uv lock --upgrade-package django`, then run `manage.py check --deploy` and the test suite against PG17. Do not bundle the two changes, so each one can be reverted on its own.

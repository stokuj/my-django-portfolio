# F-011 (risk lens): Django 5.1 is EOL with unpatched advisories

**Verdict:** CONFIRMED (not refuted). The fix ordering needs a hard guard.
**Confidence:** medium. EOL and the pin are verified. The advisory list cannot be checked from the code.
**Adjusted severity:** high (unchanged). The framework serves the public web and gets no more security releases. Direct exposure to the cited advisories looks limited: no app code uses `get_signed_cookie`/`set_signed_cookie`, `DomainNameValidator` or `django.core.cache` (grep over `django/`). But `django.contrib.messages` and `sessions` are installed (`django/config/settings.py:52-53`), and the default message storage uses signed cookies.

## Verified facts
- `pyproject.toml:10` pins `django==5.1.15`, which is the final 5.1 release. 5.1 reached EOL in Dec 2025.
- `infra/docker-compose.prod.yml:3` and `infra/docker-compose.dev.yml:3` both use `postgres:13`. Django 5.2 requires PostgreSQL 14+. Bumping first breaks prod, so the dependency on F-007 is real.
- Other 5.2 constraints are met: `asgiref==3.8.1` (`pyproject.toml:7`) meets 5.2's minimum, and Python 3.13 is supported.

## Risks in applying the fix (not covered by the finding)
1. **CI cannot catch the PG13 incompatibility, even after F-002.** The CI `.env` (`.github/workflows/django.yml:39-43`) sets no `DB_ENGINE`, so tests run on sqlite (`django/config/settings.py:111`). A Django 5.2 bump merged before the PG upgrade passes CI green.
2. **Failure mode in prod is a full outage.** On connect, Django 5.2 raises `NotSupportedError` for PG < 14. web runs `migrate && ... gunicorn` on every start (`infra/docker-compose.prod.yml:43-46`), so web exits, and so do worker and beat. Every merge to main deploys automatically. No data is lost, but the site stays down until a rollback.
3. **Lockfile.** `uv.lock` must be regenerated (`uv lock --upgrade-package django`). If only `pyproject.toml` changes, the image build can fail or drift.
4. The finding's "risk" line ("tests do not run in CI until F-002") understates this. Fixing F-002 gives coverage for the app logic, not for the database version.

## Better proposal
- Hard order: F-007 (PG upgrade and data cutover in prod) is merged and verified live first. The Django bump goes in a separate, later PR.
- Pin the latest 5.2.x patch release when you apply the fix, not a version number fixed now. Regenerate `uv.lock` in the same commit.
- Before merging, run `make verify` once with `DB_ENGINE=django.db.backends.postgresql` against the new PG version (local or dev compose), or add a Postgres service to CI. Otherwise nothing tests the 5.2+PG combination before prod does.
- Interim, if F-007 slips: no 5.1 patch exists, so the only mitigation is to keep the exposed surface small (no new signed-cookie or cache usage). Do not delay F-007.
Effort: S for the bump itself. It is gated by F-007 (M/L).

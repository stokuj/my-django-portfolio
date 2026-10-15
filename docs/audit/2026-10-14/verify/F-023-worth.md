# F-023: Two HTTP calls and nested isinstance validation where one GraphQL viewer query works

**Verdict:** CONFIRMED (with corrections)
**Confidence:** high
**Adjusted severity:** low (was medium)

## Reasoning
- `django/main/heatmap.py:82-88`: the REST `/user` call (`github_client.py:49-77`) is used only for `login`. `id` is validated (`github_client.py:72-75`) and then thrown away. The only other caller is tests (`test_heatmap.py:10,18-36`).
- `heatmap.py:83-85` checks `login` again after `github_client.py:74` already did. That is a real duplicate.
- `github_client.py:135-176` has 7 `isinstance(Mapping)` checks plus list and type checks. One `try/except (KeyError, TypeError)` around the indexing covers the same failures.
- `github_client.py:29-36`: the 4 substring ifs collapse to a single `any(...)`. This is only cosmetic.
- GraphQL `viewer { login contributionsCollection(from,to) {...} }` returns the same `ContributionsCollection` type as `user(login:)` and uses the same token. The 401/403 status mapping (`github_client.py:126-127`) and the GraphQL errors mapping (`139-140`) still apply, so auth-error behaviour stays the same.
- No documented deliberate decision. The two-call shape comes from the migration plan (`docs/superpowers/plans/2026-05-08-issue-51-heatmap-migration.md:221-270`), and no reason is recorded for it.

## Why downgrade
- The task runs hourly (Celery beat). One extra request per hour costs nothing. The gain is readability only, so this is low, not medium.

## Correction to the proposal
- Do NOT delete the type check at `heatmap.py:39-41` without moving it elsewhere. `build_weeks_payload` runs inside the try at `heatmap.py:81-93`, but that try catches only `GitHubAuthError` and `GitHubUpstreamError`. A non-int count (`count <= 0`, line 21) or a non-str date (`fromisoformat` raises TypeError, not ValueError) would then raise an uncaught TypeError out of the Celery task, where today the day is skipped. Validate in exactly one place, either the client's try/except mapped to `GitHubUpstreamError` or `build_weeks_payload`, not in both and not in neither.
- Behaviour change to accept: today malformed individual days are skipped silently (`github_client.py:164-176`). A single try/except fails the whole fetch instead. That is fine, because the snapshot keeps its last good data, but it is a change.
- "About -70 lines" is optimistic. A realistic net is about -40 to -50 in src. Tests also change: `test_heatmap.py:18-36` deleted, `171-249` re-mocked.

## Better proposal (smallest diff)
1. Change the query to `viewer { login contributionsCollection(...) }`, drop the `$login` variable, and return `(login, days)` from `fetch_contribution_days`.
2. Delete `fetch_authenticated_user` and `heatmap.py:82-86`.
3. Replace `github_client.py:143-176` with one try/except (KeyError, TypeError) that raises `GitHubUpstreamError`. Keep the per-day `isinstance` filter, or keep `heatmap.py:39-41`, but only one of them.
4. Optional: use `any()` for the substrings. Effort: S-M.

# F-023 (reproduce): Two HTTP calls and nested isinstance validation where one GraphQL viewer query works

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (simplification of code that works; no bug or security impact)

## Reasoning
- `django/main/github_client.py:49-77` `fetch_authenticated_user` makes a REST `GET /user` call. Its only caller is `django/main/heatmap.py:82`, which uses only `login` (`heatmap.py:83-86`). The returned `id` (`github_client.py:72-77`) is not used anywhere outside tests.
- `github_client.py:89-104` then sends a separate GraphQL `user(login: $login)` query. A single `viewer { login contributionsCollection(from:, to:) {...} }` query returns the same calendar for the token owner, so one round trip is enough.
- `github_client.py:131-178` has exactly 7 `isinstance(..., Mapping)` checks (lines 135, 144, 148, 152, 156, 165, 171), plus 2 list checks (160, 168) and a type check on each day (175).
- `heatmap.py:83-85` checks `login` again even though `github_client.py:74-75` already guarantees a non-empty str. `heatmap.py:39-41` checks the day types again even though `github_client.py:175` already filters them. `build_weeks_payload` gets its input only from `fetch_contribution_days` (`heatmap.py:88-89`).
- `github_client.py:29-36` has 4 separate substring `if`s that one `any(...)` can replace.
- Tests that depend on the current shape: `django/main/tests/test_heatmap.py:18-36` (`fetch_authenticated_user`), and lines 172, 229 and 238 (patch `main.heatmap.fetch_authenticated_user`). The risk note about rewriting mocks is accurate.

## Caveats on the proposal
- Keep the `errors` / auth-failure check (`github_client.py:137-141`) before indexing. GraphQL returns `data: null` together with `errors` on bad credentials, and that case must still raise `GitHubAuthError`.
- A single `try/except (KeyError, TypeError)` changes behaviour in one way: right now a malformed week or day is skipped (`165-172`). After the change, the whole fetch would fail. GitHub's schema makes this practically irrelevant, but the change is not strictly behaviour-preserving.
- "About -70 lines" is optimistic. A realistic estimate is 50-60 lines.

## Better proposal
Write one `fetch_heatmap(token)` in `github_client.py` that does the following:
1. POST a `viewer { login contributionsCollection { contributionCalendar { weeks { contributionDays { date contributionCount }}}}}` query.
2. Keep the status-code and `errors` handling, with `any()` over the auth substrings.
3. Run `login = d["viewer"]["login"]; days = [... for w in ...weeks for d in w["contributionDays"]]` inside `try/except (KeyError, TypeError) -> GitHubUpstreamError`.
4. Delete `fetch_authenticated_user` and the re-checks at `heatmap.py:83-85` and `heatmap.py:39-41`.

Effort: S-M.

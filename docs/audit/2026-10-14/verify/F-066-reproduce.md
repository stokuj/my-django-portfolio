# F-066 (reproduce lens): GitHub client and heatmap error mapping partly untested

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning (verified at HEAD)
- `fetch_authenticated_user` (django/main/github_client.py:49-77) has exactly two tests: happy path and 401 (django/main/tests/test_heatmap.py:18-36). Untested branches: 403 (:60), >=400 upstream (:62-63), network/timeout (:57-58), invalid JSON (:65-68), non-mapping payload (:69-70), missing/invalid `id`/`login` (:72-75).
- `fetch_contribution_days`: tests cover flatten, timeout, and auth-type GraphQL errors (test_heatmap.py:38-111). The non-auth GraphQL error path (github_client.py:141) is untested, as are HTTP status branches (:126-129), invalid JSON (:131-136) and the missing `data/user/...` guards (:143-161).
- `fetch_heatmap_data` (django/main/heatmap.py:68-99): tests cover success and two `GitHubAuthError` mappings (test_heatmap.py:169-249). The `GitHubUpstreamError` -> "Heatmap service is temporarily unavailable." mapping (heatmap.py:92-93) is untested; grep finds that string in no test.
- No-token path (heatmap.py:77-79): the "Heatmap is not configured." tests in test_views.py:304-310 and test_tasks.py:296-333 patch `get_configured_github_token` in the caller, and both callers short-circuit before calling `fetch_heatmap_data` (django/main/views.py:148-152, django/main/tasks.py:~120-143). So heatmap.py:78-79 is never exercised by tests, and is effectively only reachable by a direct call (defensive branch).
- Lower-level grep: `main.github_client` is only imported by test_heatmap.py; no other test covers these branches.

## Why severity stays low
All untested branches are simple raise/return mappings; their failure modes are caught upstream by the caller's `(payload, error)` contract and view/task tests that mock `fetch_heatmap_data` with an error string (test_views.py:281). Gap is real but cheap and low-risk.

## Better proposal (smaller)
- One `subTest` loop in the existing 401 test over `(401, AuthError), (403, AuthError), (500, UpstreamError)`.
- One test: `fetch_heatmap_data` with `fetch_authenticated_user` patched to raise `GitHubUpstreamError` -> asserts the "temporarily unavailable" message (this covers the only user-visible mapping not yet tested).
- Optionally one test for non-auth GraphQL errors (github_client.py:141). Skip invalid-JSON / missing-field cases; they are trivial guards.
- Skip the no-token test for `fetch_heatmap_data`: both callers already gate on the token.

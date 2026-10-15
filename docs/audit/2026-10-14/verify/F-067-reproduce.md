# F-067 — GitHub rate-limit 403 reported as "token invalid or expired"

- Verdict: CONFIRMED (partially; 429 part is wrong)
- Confidence: high
- Adjusted severity: low

## Reasoning
- `django/main/github_client.py:60-61` and `:126-127` map every 403 to `GitHubAuthError` without inspecting headers.
- `django/main/heatmap.py:90-91` turns `GitHubAuthError` into "Configured GitHub token is invalid or expired." So a primary rate-limit 403 (`X-RateLimit-Remaining: 0`) or secondary rate-limit 403 (`Retry-After`) produces a misleading "rotate token" message.
- 429 is NOT misreported: it falls through to `status_code >= 400` -> `GitHubUpstreamError` (`github_client.py:62-63`, `:128-129`) -> "temporarily unavailable". The finding's "403/429" wording overstates this.
- Practical impact is small: the task makes 2 calls/hour (hourly beat refresh) against a 5000/h authenticated budget, so rate limiting only happens if the token is shared with other heavy consumers. Message is cosmetic; no data loss.

## Better proposal
Keep 429 as is. Add one helper used at both sites before the 401/403 check:
`if response.status_code == 403 and (response.headers.get("X-RateLimit-Remaining") == "0" or "Retry-After" in response.headers): raise GitHubUpstreamError("GitHub rate limit exceeded")`
(covers secondary limits, which do not always set Remaining=0). One test with a mocked 403 + header asserting `GitHubUpstreamError`.

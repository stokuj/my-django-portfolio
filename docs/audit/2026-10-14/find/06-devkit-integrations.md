# devkit-integrations

Scope: `django/main/{heatmap,github_client,markdown_sync,context_processors,validators,admin,middleware}.py` plus direct callers (`views.about_heatmap_data`), HEAD `4416049`. Behavioural findings proven in a scratch worktree (removed afterwards).

**Verdict:** CHANGES NEEDED (2 confirmed, 1 verified ops gap, 2 simplifications)

## 1. Public heatmap endpoint retries GitHub on every request while refresh fails
- **Severity:** medium · **Category:** performance · **Effort:** S
- **Location:** `django/main/views.py:157-163` (caller of `heatmap.fetch_heatmap_data`, `heatmap.update_snapshot_error` at `django/main/heatmap.py:159-171`)
- **Problem:** On failure only `last_error` is saved; `fetched_at` stays stale, so every anonymous GET `/about/heatmap-data/` makes 2 synchronous GitHub calls (timeouts 15s + 20s) during an outage, bad token or rate limit. Blocks Gunicorn workers and burns the token's rate limit. No backoff.
- **Proof (fails on HEAD `3 != 1`, passes with fix):**
  ```python
  @patch("main.views.get_configured_github_token", return_value="gho_x")
  @patch("main.views.fetch_heatmap_data", return_value=(None, "upstream failure"))
  def test_failed_refresh_is_not_retried_on_every_public_request(self, fetch_mock, _tok):
      for _ in range(3):
          self.client.get(reverse("about_heatmap_data"))
      self.assertEqual(fetch_mock.call_count, 1)
  ```
- **Proposal:** Gate the sync fetch with a cooldown, e.g. `cache.add("heatmap-refresh-cooldown", 1, 300)` before calling `fetch_heatmap_data()`; when skipped, serve the snapshot or 503 with `last_error`. (Verified: existing view tests pass with the fix once `cache.clear()` is added to `ViewsTest.setUp`.) Alternative: never fetch synchronously from the public view; rely on the hourly beat task.
- **Risk:** Low. LocMem cache is per-process, so the cooldown is per Gunicorn worker; good enough as a cap.

## 2. GitHub rate-limit 403 reported as "token invalid or expired"
- **Severity:** low · **Category:** bug · **Effort:** S
- **Location:** `django/main/github_client.py:60-61`, `django/main/github_client.py:126-127`
- **Problem:** GitHub returns 403 (or 429) with `X-RateLimit-Remaining: 0` when rate-limited. Any 403 raises `GitHubAuthError`, so `heatmap.py:90-91` stores "Configured GitHub token is invalid or expired." in `HeatmapSnapshot.last_error` / `TaskExecutionStatus`, sending the admin to rotate a valid token.
- **Proof (raises `GitHubAuthError` on HEAD, passes with fix):**
  ```python
  @patch("main.github_client.requests.get")
  def test_rate_limited_403_is_upstream_not_auth_error(self, get_mock):
      get_mock.return_value = Mock(status_code=403, headers={"X-RateLimit-Remaining": "0"})
      with self.assertRaises(GitHubUpstreamError):
          fetch_authenticated_user("gho_valid_but_rate_limited")
  ```
- **Proposal:** Before the 401/403 check in both functions:
  ```python
  if response.status_code == 429 or (
      response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0"
  ):
      raise GitHubUpstreamError("GitHub rate limit exceeded")
  ```
- **Risk:** Low. Existing `test_heatmap` suite passes with the fix.

## 3. Session table grows without bound (no `clearsessions`)
- **Severity:** medium · **Category:** ops · **Effort:** S
- **Location:** `django/main/middleware.py:15-17`; `django/config/settings.py` (no `SESSION_ENGINE`, no cleanup in `CELERY_BEAT_SCHEDULE`)
- **Problem:** Every cookie-less hit on `/` or `/home/` (crawlers, uptime probes) writes `session["has_visited"]`, creating a `django_session` row (DB backend default) and incrementing the visitor counter. `clearsessions` is not referenced anywhere in the repo, so expired rows are never purged.
- **Proof (fails on HEAD `5 not less than or equal to 1`):**
  ```python
  def test_cookieless_home_hits_do_not_create_one_session_row_each(self):
      for _ in range(5):
          Client().get("/")
      self.assertLessEqual(Session.objects.count(), 1)
  ```
  (Shows growth per hit; the missing cleanup is verified by `grep -rn clearsessions` returning nothing.)
- **Proposal:** Add a daily beat task that runs `call_command("clearsessions")`. Caps the table at `SESSION_COOKIE_AGE` (2 weeks) worth of hits.
- **Risk:** None for users; only expired sessions are removed.

## 4. Redundant exception handling around `requests`
- **Severity:** low · **Category:** simplification · **Effort:** S
- **Location:** `django/main/github_client.py:57`, `:123`; `django/main/markdown_sync.py:107-110`, `:154-155`
- **Problem:** `requests.Timeout` is a subclass of `RequestException`, which is a subclass of `OSError` (verified: `issubclass(requests.RequestException, OSError) is True`). So `except (requests.Timeout, requests.RequestException)` lists a redundant class, the `HTTPError` re-raise plus `OSError` re-wrap in `_download_markdown` changes nothing a caller catches, and `(HTTPError, RequestException, UnicodeDecodeError, ValueError, OSError)` collapses to `(OSError, ValueError)`.
- **Proposal:** `except requests.RequestException` in github_client; drop the try/except around `requests.get` in `_download_markdown` (keep `raise_for_status()`); catch `(OSError, ValueError)` in `sync_project_markdown`.
- **Risk:** None. Behaviour is unchanged.

## 5. Dead re-validation of login in `fetch_heatmap_data`
- **Severity:** low · **Category:** simplification · **Effort:** S
- **Location:** `django/main/heatmap.py:83-86`
- **Problem:** `fetch_authenticated_user` already guarantees a non-empty `str` login (`github_client.py:74-75`); the second check cannot trigger.
- **Proposal:** `username = fetch_authenticated_user(token)["login"]`.
- **Risk:** None.

Not reported (checked, no proven defect): `validators.py` (rejects non-https, other hosts, query/fragment, non-root paths); `context_processors.py` (3 small queries per render, acceptable); `admin.py`; `markdown_sync.py` URL building and HTML/size guards.

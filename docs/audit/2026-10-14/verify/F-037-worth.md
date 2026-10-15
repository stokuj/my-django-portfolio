# F-037 - Markdown download guards untested; mock skips the Content-Length path

**Lens:** worth
**Verdict:** CONFIRMED (partly; proposal adjusted)
**Confidence:** high
**Adjusted severity:** low (was medium)

## Facts verified at HEAD
- `django/main/tests/test_markdown_sync.py:19` sets `resp.headers = {}`, so `markdown_sync.py:112-121` (Content-Length branch) never runs.
- The test file has 3 tests only (success :48, connection error :74, oversized body :100). No test anywhere in `django/main/tests/` covers HTML rejection (`markdown_sync.py:130`), fallback after 404 (`:149-157`), non-GitHub host (`:49`), `no_candidate_urls` (`:137`) or `UnicodeDecodeError` (`:129`). Grep of the tests dir finds only view/url tests for the task endpoint.

## Why the proposal is only partly worth doing
- The Content-Length guard protects nothing. `requests.get` at `markdown_sync.py:101` has no `stream=True`, so the whole body is already in memory before the header is read at `:112`. The body check at `:124` already catches oversized payloads and is tested (`test_markdown_sync.py:100`). A test for `:112-121` would lock in dead code. Better: delete `:112-121`. Only add `stream=True` plus a capped read if a real memory limit is needed (not justified for a personal portfolio README sync).
- Worth testing, cheaply, with the existing helper and no `headers` parameter:
  1. 404 on the first candidate, 200 on the second -> `updated=True`, `source_url` is the second URL (the main logic in `:149-157`).
  2. Body starts with `<!DOCTYPE html` -> `download_failed`, old file kept (`:130`).
- Low value / skip: `no_candidate_urls` and non-GitHub host (pure early returns), `UnicodeDecodeError` (same `except` branch as the other errors at `:154-155`).
- Severity: the failure mode of every untested guard is "keep the old file and log a warning", so there is no data loss risk. Low, not medium.

## Better proposal
Delete the dead Content-Length block (`markdown_sync.py:112-121`). Add two tests to `test_markdown_sync.py`: 404-then-200 fallback, and HTML-body rejection. Leave `_make_mock_response` as is. Effort S.

Side note (out of scope): the `except HTTPError: raise` / `RequestException -> OSError` rewrap at `:107-110` is redundant, because the caller at `:154-155` catches all of these anyway.

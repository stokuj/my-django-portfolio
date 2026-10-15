# F-037 - Markdown download guards untested; mock skips the Content-Length path

**Verdict:** CONFIRMED (reproduce lens)
**Confidence:** high
**Adjusted severity:** low (test gap only, no defect in production code)

## Reasoning
- `django/main/tests/test_markdown_sync.py:19` - `_make_mock_response` hard-codes `resp.headers = {}`, so `headers.get("Content-Length")` at `django/main/markdown_sync.py:112` is always `None`; lines 113-121 never run.
- Only 3 tests exist (`test_markdown_sync.py:48,74,100`): success, ConnectionError on every call, oversized body (hits the `len(raw_bytes)` check at `markdown_sync.py:124`, not the header check).
- No test anywhere in `django/main/tests/` or `tests/` (grep for `_download_markdown`, `build_markdown_candidate_urls`, `_parse_github_owner_repo`, `no_candidate_urls`, `expected Markdown`) covers:
  - HTML rejection (`markdown_sync.py:130-131`)
  - fallback to the next candidate after one fails (`:149-157`); the failure test fails every candidate
  - non-GitHub host (`:49-50`)
  - `no_candidate_urls` (`:137-143`)
  - `UnicodeDecodeError` from `decode("utf-8-sig")` (`:129`, caught at `:155`)
- `test_views.py:527-606` only tests the admin endpoint that enqueues the task, not these guards.

## Why severity drops to low
All listed branches look correct on reading; nothing is broken. It is coverage, not a bug.

## Better proposal
The Content-Length guard (`markdown_sync.py:112-121`) adds no protection: `requests.get` is called without `stream=True` (`:101`), so the full body is already in memory before the header is checked, and `:124` repeats the same check on the real size. Delete lines 112-121 instead of writing a test for them (or switch to `stream=True` with a capped read, if a memory limit is really needed). Then add short tests only for the guards that do something: HTML rejection, fallback after a 404 on the first candidate, and `no_candidate_urls` (a non-GitHub `github_url` plus empty profile `github_url` covers `:49` as well). A UnicodeDecodeError test is optional.

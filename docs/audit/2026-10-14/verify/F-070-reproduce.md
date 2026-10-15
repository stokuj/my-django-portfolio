# F-070 (reproduce): Redundant exception handling around requests, duplicate size check, hand-rolled dedup

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (simplification, effort S)

## Reasoning
Checked against requests 2.33.0 installed in the project venv:
`RequestException.__mro__ = (RequestException, OSError, Exception, ...)`; `Timeout` and `HTTPError` are subclasses of `RequestException`; `UnicodeDecodeError` is a subclass of `ValueError`.

- `django/main/markdown_sync.py:100-110`: `except HTTPError: raise` followed by `except RequestException: raise OSError(str(exc))` only turns one OSError subclass into a plain OSError with the same `str()`. The only caller (`markdown_sync.py:151`) catches OSError anyway and logs/stores `str(exc)` (`:156-157`), so its output stays the same.
- `markdown_sync.py:154-155`: `(HTTPError, RequestException, UnicodeDecodeError, ValueError, OSError)` is the same as `(OSError, ValueError)`.
- `django/main/github_client.py:57,123`: `(requests.Timeout, requests.RequestException)` is the same as `requests.RequestException`.
- `markdown_sync.py:112-121`: `requests.get` is called without `stream=True` (`:101-105`), so the whole body is already in memory before the Content-Length header is read. The real limit is the `len(response.content)` check at `:123-127`, which has a test (`tests/test_markdown_sync.py`, oversized-download test; mock headers are `{}`, so the pre-check is never exercised). The only behaviour difference is that a header which overstates the length rejects an otherwise small body. That edge case does not matter.
- `markdown_sync.py:90-96`: an order-preserving dedup loop, which is exactly `list(dict.fromkeys(candidates))`.

The existing tests (ConnectionError side effect, oversized payload, requests.Timeout in test_heatmap) still pass once the simplification is made, because every exception they raise is still caught.

## Better proposal
Same as the finding: delete the try/except around `requests.get` (`:100-110`) and the Content-Length block (`:112-121`), use `return list(dict.fromkeys(candidates))`, catch `(OSError, ValueError)` at `:154`, and catch `requests.RequestException` at `github_client.py:57,123`. If a real early size cap is ever wanted, it needs `stream=True` with a bounded `iter_content` read. YAGNI for README files from GitHub.

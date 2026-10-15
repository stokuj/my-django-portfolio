# F-003 (reproduce): Markdown sync rewrites the file every run and the filename keeps growing

**Verdict:** CONFIRMED (severity overstated)
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `django/main/markdown_sync.py:168-172`: no content comparison; every successful download calls `markdown_file.save(Path(old_name).name, ...)` while the old file still exists in `blog_markdown/`.
- `django/main/models.py:60-65`: plain `FileField(upload_to="blog_markdown/")`, default `FileSystemStorage` (no `STORAGES` override in `django/config/settings.py`), so `get_available_name` appends `_XXXXXXX`.
- `django/main/models.py:251-262`: `pre_save` sees a different name and deletes the old file.
- Reproduced with Django 5.1.15 `FileSystemStorage` (scratch script outside repo): `sync-success.md -> sync-success_wmxhhyC.md -> ..._LcgtPHC.md -> ...`, +8 chars per run, reaching 100 chars after 9 runs; after that Django truncates and the name stays at 100 (no crash).
- Race: `views.py:340-354` `_load_project_markdown` catches `OSError` and returns `None`, so a request holding the old name between delete and its read gets empty content. Window is milliseconds every 2h; real but rare.
- `django/main/tests/test_markdown_sync.py:48-70` asserts only content, not the name.

## Why not high
No data loss, no exploit. Filename is not user-facing (blog served via view by `blog_url`). Impact: needless disk churn every 2h, ugly/truncated names, a rare empty render.

## Better proposal
The proposed "save to fixed name" does not work alone: `FileField.save` to an existing name still gets a suffix. Simpler:
1. Read current content; if equal to `markdown_text`, return `updated: False, reason: "unchanged"` (counters: treat as success).
2. If changed and a file exists, overwrite in place with `project.markdown_file.storage.open(name, "wb")` (name unchanged, no model save, no signal delete). Only use `markdown_file.save(...)` when no file exists yet.
3. Test: two syncs with different content keep the same `markdown_file.name`; a sync with same content does not rewrite.

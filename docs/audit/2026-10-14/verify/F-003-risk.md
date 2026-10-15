# F-003 (risk lens): Markdown sync rewrites the file every run and the filename keeps growing

**Verdict:** CONFIRMED (bug real), but severity overstated and the proposed fix is flawed.
**Confidence:** high
**Adjusted severity:** medium

## Bug: confirmed
- `django/main/markdown_sync.py:167-170` reuses the *current* basename (`Path(old_name).name`) and calls `markdown_file.save()` unconditionally. Because that file already exists, `FileSystemStorage` (default; no `STORAGES` in settings) appends `_XXXXXXX`. Each run starts from the already-suffixed name, so the name grows.
- `django/main/models.py:251-262` (`pre_save`) deletes the old file once the name differs. This runs every 2h even when the README has not changed.
- The race exists: `views.py:340-354` opens `project.markdown_file` by name. A request that loaded the old name returns `None`, which renders an empty body. The window is tiny, though.
- `test_markdown_sync.py:48-71` checks only the content.

## Why not high
- No data loss: the content is re-downloaded each run. Growth is bounded because `get_available_name` truncates to `max_length` (100). The race lasts milliseconds on a low-traffic portfolio page. It is wasteful churn with a cosmetic or rare impact, so medium.

## Risks in the proposed fix
1. **"Save to fixed name" does not give a stable name.** I reproduced this with Django 5.1.15 `FileSystemStorage`: saving to `slug.md` while `slug.md` exists gives `slug_7SFO63H.md`. On the next run `slug.md` is free again, so the name alternates `slug.md <-> slug_XXXX.md`. The proposed test "name stable across two syncs" would FAIL. Growth stops, but the churn and the race remain.
2. **Overwrite in place** (`allow_overwrite=True`, new in Django 5.1) is not safe as a global setting. Admin uploads to `thumbnails/` and `blog_markdown/` with the same filename would silently overwrite another project's file. A per-field `storage=` changes the field deconstruct, which needs a migration. It is also a non-atomic write, so a reader can see a partial file.
3. **"Unchanged" result vs task counters:** `tasks.py:58-62` counts `failed = len(results) - updated_count`. Returning `updated: False` for unchanged content marks the run failed or partial. Return `updated: True` (or add a `skipped` key counted as success).
4. **Comparison read must tolerate a missing file:** after a volume reset, the DB name exists but the file does not. Reading it must catch `OSError` and treat the content as changed, or the sync crashes.

## Better proposal (S)
- Before saving, read the stored file (catch `OSError` and treat it as changed). If the bytes equal `markdown_text`, return success without writing. This removes the 2h churn and the race in the normal case.
- When the content changed, save under `f"{project.blog_url or f'project-{project.id}'}.md"` (not the current basename). The name then alternates between two values and stops growing. Accept that, or document it. Do not use `allow_overwrite`.
- Tests: (a) a second sync with identical content leaves the name and mtime unchanged; (b) a sync with new content removes the old file and the name length does not grow over 3 syncs. Do not assert that the name is identical.

# F-003 (worth lens): Markdown sync rewrites the file every run and the filename keeps growing

**Verdict:** CONFIRMED (bug is real; severity overstated; proposal needs a correction)
**Confidence:** high
**Adjusted severity:** medium

## Reasoning
- `django/main/markdown_sync.py:168-172` reuses `Path(old_name).name` (including earlier random suffixes) and calls `markdown_file.save()` while the old file still exists, so `FileSystemStorage.get_available_name` appends `_XXXXXXX`. The old file is deleted only afterwards by the `pre_save` signal (`django/main/models.py:251-262`).
- Reproduced with Django 5.1.15 `FileSystemStorage` in a temp dir: `my-project.md` -> `my-project_Ay16e5j.md` -> ... grows by 8 chars per run and caps at 100 chars (Django truncates `file_root`), then keeps rewriting with a fresh suffix. No crash, no data loss.
- The write happens every run (beat every 2h) even when the content is unchanged; there is no comparison.
- Race: `_load_project_markdown` (`django/main/views.py:340-354`) catches `OSError` and returns `None`, so a request holding the old name after the delete renders an empty body. Real, but the window is milliseconds every 2h.
- Test gap confirmed: `django/main/tests/test_markdown_sync.py:48-72` checks only the content.
- No docs/git-log decision justifies the current naming (code from `335e524`, unrelated commit message).

Why not high: nothing exploitable, nothing lost, name self-caps at 100. Ugly churn plus a tiny race = medium.

## Problems with the proposal
1. "Save to the fixed name" alone does NOT fix the growth: the old file under that name still exists at `storage.save()` time, so Django suffixes it again. The old file must be removed first (or storage must allow overwrite).
2. "Skip the write when unchanged" must still report success. `django/main/tasks.py:58-62` counts every `updated=False` result as failed, so returning `updated=False` for unchanged would flip the task to PARTIAL_SUCCESS/FAILURE.

## Better proposal (smallest diff, in `sync_project_markdown`)
```python
target = f"blog_markdown/{project.blog_url or f'project-{project.id}'}.md"
data = markdown_text.encode("utf-8")
storage = project.markdown_file.storage
if project.markdown_file.name == target and storage.exists(target):
    with storage.open(target, "rb") as fh:
        if fh.read() == data:
            return {..., "updated": True, "unchanged": True, ...}
if storage.exists(target):
    storage.delete(target)
project.markdown_file.save(Path(target).name, ContentFile(data), save=False)
project.save(update_fields=["markdown_file"])
```
The skip-if-unchanged branch removes almost all writes (and with them the race). On first migration from a suffixed name, `pre_save` still removes the old suffixed file. Test: two syncs with different content keep `blog_markdown/<slug>.md` and leave exactly one file in `blog_markdown/`; a sync with identical content reports success and does not touch mtime.
Effort: S.

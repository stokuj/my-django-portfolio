# F-026 (worth): Media file deleted even when the DB transaction rolls back

**Verdict:** CONFIRMED (mechanism real), but overstated. **Confidence:** medium. **Adjusted severity:** low.

## Reasoning
- The mechanism is real. `_delete_file_field` (django/main/models.py:237-241) calls `storage.delete()` right away from `post_delete` (245-248) and from `pre_save` (251-262). Neither call is tied to the transaction. Django admin's `changeform_view` and `delete_view` run inside `transaction.atomic`, so if the request rolls back after the signal fires, the row still points at a file that no longer exists.
- The trigger the finding names is mostly wrong. `blog_url` (models.py:71) is not `unique=True`. It has a conditional `UniqueConstraint` (models.py:94-100). Since Django 4.1, `ModelForm.full_clean()` runs `validate_constraints()`, and this project uses Django 5.1.15 (pyproject.toml:10). So the admin form rejects a duplicate slug before `save()` runs, and an IntegrityError is only possible from a concurrent race. On a single-admin portfolio that is close to impossible. The other ways to roll back after `pre_save` (failures in `save_related` or `log_change`) are rare too.
- The impact is small:
  - A lost `markdown_file` comes back on the next `sync_project_markdown` run (markdown_sync.py:168-172, every 2h). That run writes a fresh file and saves its name.
  - Only a lost thumbnail needs a manual re-upload.
  - "Data loss" in a rare race on a one-user admin fits low, not medium.
- The proposed fix is only partly correct. Outside an atomic block (autocommit: the Celery markdown sync at markdown_sync.py:172, the shell), `transaction.on_commit` runs the callback immediately. `pre_save` fires before `Model.save_base` opens its rollback context. So in `pre_save` the deferred delete still runs before the UPDATE, and if that UPDATE fails, the file is still gone. The fix only helps inside an outer atomic block, such as admin.
- Test cost is confirmed. `ProjectMediaCleanupTests` (tests/test_models.py:264-309) is a `TestCase`, so its `on_commit` callbacks never fire. Both assertions (298, 309) would fail without `captureOnCommitCallbacks(execute=True)`. No markdown_sync test checks that the old file is deleted (test_markdown_sync.py:85-125 only cover failure paths).

## Better proposal (if done at all)
- Keep the `post_delete` handler, but wrap its delete in `transaction.on_commit`. `post_delete` fires after the DELETE, so this placement is correct.
- For replacements, stash the old names in `pre_save` (for example `instance._stale_files = [...]`) and delete them from a `post_save` receiver through `transaction.on_commit`. That runs after the UPDATE succeeds, in both admin and autocommit paths.
- About 10 lines, plus `captureOnCommitCallbacks(execute=True)` in the two existing tests.
- Alternative: drop it. `django-cleanup` already does exactly this with `on_commit`, but a new dependency is not worth it for two FileFields. Given the low impact, deferring is reasonable.

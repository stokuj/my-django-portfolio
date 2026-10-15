# F-026 (reproduce lens): Media file deleted even when the DB transaction rolls back

**Verdict:** CONFIRMED (the pattern exists), but the trigger named in the finding is mostly unreachable, so severity is lower.
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/models.py:238-242`: `_delete_file_field` calls `storage.delete()` right away, with no `transaction.on_commit`.
- `django/main/models.py:245-248`: `post_delete` deletes the files inside the caller's transaction.
- `django/main/models.py:251-262`: `pre_save` deletes the old file **before** the UPDATE runs. If that UPDATE or anything later in the same atomic block fails, the row keeps pointing at a missing file.
- Django admin `changeform_view` and `delete_view` run inside `transaction.atomic`, and the repo adds no other `atomic` blocks (grep). So a rollback after the delete is possible in principle.
- **The named trigger is mostly unreachable.** Django is 5.1.15 (`pyproject.toml:10`), and since 4.1 `ModelForm._post_clean` runs `validate_constraints()`. That means `uniq_project_blog_url_when_present` (`models.py:94-99`) is checked at form validation, before `save()` and before `pre_save` fires. An IntegrityError on `blog_url` through the admin needs a concurrent race between two saves.
- The "probe test" most likely called `save()` directly inside `atomic`, which bypasses form validation. That shows the mechanism, not a realistic admin path.
- What can still cause a rollback: a DB error during the UPDATE, `save_related` (m2m `tags`), or `log_change`. All are rare in a single-admin portfolio.
- `markdown_sync.py:168-172` runs outside atomic (autocommit), and storage gives a new name when one is taken. That path is unaffected.

## Better proposal
The proposed `on_commit` deferral in `_delete_file_field` is correct and minimal. Capture `name` and `storage` before the lambda, as the proposal does. With no transaction (the markdown_sync path), `on_commit` runs the callback at once, so that path behaves the same. `ProjectMediaCleanupTests` (`django/main/tests/test_models.py:264`) runs inside a `TestCase` atomic block, so it needs `self.captureOnCommitCallbacks(execute=True)`. Effort S. Low priority.

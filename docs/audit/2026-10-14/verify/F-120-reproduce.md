# F-120 - Admin .md upload validated only by extension and silently overwritten by sync

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (unchanged)

## Reasoning

- `django/main/models.py:58-63`: `markdown_file` has only `FileExtensionValidator(["md"])`, no `help_text`. `django/main/admin.py:13-19` lists the field with no custom form, so nothing else validates it.
- Sync path is stricter: `django/main/markdown_sync.py:112-128` (size cap `MAX_MARKDOWN_SIZE_BYTES`, line 11), `:130` UTF-8 decode, `:131-132` HTML rejection.
- Non-UTF-8 upload: `django/main/views.py:340-349` returns `None` on `UnicodeDecodeError`; `views.py:402-403` passes it on; `templates/projects/detail.html:11-21` shows "No markdown content available for this project yet." Not literally an empty page, but the content is silently dropped with no error to the admin.
- Overwrite: `django/main/tasks.py:36` selects every `blog=True` project; `markdown_sync.py:168-170` saves the downloaded README over the field. Precondition the finding omits: overwrite happens only if `build_markdown_candidate_urls` (`markdown_sync.py:68-96`) returns URLs (project `github_url` on github.com, or an active profile `github_url` plus repo path) AND a download succeeds (`:151-163` returns early otherwise). With a profile GitHub URL set this covers practically every blog project.
- Size: `DATA_UPLOAD_MAX_MEMORY_SIZE` (`django/config/settings.py:179`) does not apply to file uploads in Django, so the admin upload has no app-level size cap (the comment there is misleading). Admin-only, so not a security issue.

## Better proposal

Keep it minimal: a UTF-8 decode validator on `markdown_file` plus `help_text` ("Replaced by the GitHub README on sync when Blog is on and a repo is resolvable"). The size validator is optional; uploader is a trusted admin. Both changes produce an `AlterField` migration (no schema change).

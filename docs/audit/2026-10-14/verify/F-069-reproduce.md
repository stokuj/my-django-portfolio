# F-069 — Hard-coded BLOG_REPO_PATHS duplicates Project.github_url (reproduce lens)

**Verdict:** CONFIRMED (with corrections)
**Confidence:** high (code); data state unverifiable from repo
**Adjusted severity:** low

## Reasoning
- `django/main/markdown_sync.py:13-25` hard-codes an 11-entry slug -> repo-name map; `get_repo_path` (`:28-29`) falls back to `project.blog_url`.
- `Project.github_url` exists (`django/main/models.py:72-77`, validated by `validate_github_repo_url`), so the map duplicates data the model can already hold.
- Correction 1: the map is NOT used "only for projects without github_url".
  - `build_markdown_candidate_urls` (`markdown_sync.py:80-88`) appends `<profile user>/<repo_path>` candidates unconditionally, even when `github_url` produced candidates at `:71-78`.
  - `build_readme_url` (`:59`) computes `repo_path` before the `github_url` check (wasted call).
  - `blog_detail` (`django/main/views.py:404`, `:416`) passes `repo_path` to `projects/components/project_footer.html:6`, which builds the "Source code on GitHub" link as `{{ profile_github_base }}/{{ repo_path }}` for every blog project, ignoring `project.github_url`.
- So deleting the dict as proposed would also change the footer link; the proposal misses that consumer.
- No tests reference `BLOG_REPO_PATHS`/`get_repo_path` directly (grep of `django/main/tests`), so removal is low-risk test-wise.

## Better proposal
1. Check prod data: every `blog=True` project has `github_url` set (admin or data migration for the 11 slugs).
2. Delete `BLOG_REPO_PATHS`, `get_repo_path`, `_active_github_username` and the fallback block (`markdown_sync.py:80-88`, `:59`, `:63-65`).
3. Footer: use `{{ project.github_url }}` (or `readme_url`) instead of `profile_github_base/repo_path`; drop `repo_path` from `blog_detail` context (`views.py:404`, `:416`) and the template include (`detail.html:31`).
Effort: M (S for code, data backfill is the real cost).

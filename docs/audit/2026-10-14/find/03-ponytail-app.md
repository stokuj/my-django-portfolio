# ponytail-app

Scope: over-engineering audit of `django/` (main app, config, templates, static/js) at `dev` HEAD (4416049). Lens: ponytail-audit (delete / stdlib / native / yagni / shrink). Correctness and security are out of scope; any noted here are side observations.

---

### 1. Task status bookkeeping copy-pasted 4x, plus a redundant "no token" branch
- **Severity:** medium | **Category:** simplification | **Effort:** S
- **File:** django/main/tasks.py:119-143 (also 67-101, 145-169, 171-190, 210-246)
- **Problem:** Every task sets the same 8 fields and repeats the same 8-item `update_fields` list (5 copies), then calls `_log_task_execution`. In `refresh_portfolio_heatmap_cache_task`, the `if not get_configured_github_token()` branch (25 lines) is a no-op duplicate: `fetch_heatmap_data()` already returns `(None, "Heatmap is not configured.")` (heatmap.py:78-79), and the `if error:` branch right below does exactly the same writes.
- **Proposal:** Delete tasks.py:119-143. Add one `_record(task_name, status, total, updated, failed, error="")` helper that sets fields, calls `status.save()` and writes the log row, and call it from all three tasks. About -90 lines.
- **Risk:** Low. test_tasks.py asserts on field values, not on how they are set.

### 2. Dead self-rescheduling path (`schedule_next`)
- **Severity:** medium | **Category:** simplification | **Effort:** S
- **File:** django/main/tasks.py:113, 142, 168, 192, 250-257; django/main/views.py:189-197; django/config/settings.py:218
- **Problem:** Every caller passes `schedule_next=False` (beat at settings.py:218, admin view at views.py:452), so `_maybe_schedule_next_refresh` never runs. `views._schedule_next_heatmap_refresh` has zero callers. Beat already runs the task every hour, so self-rescheduling is not needed.
- **Proposal:** Delete the `schedule_next` parameter, `_maybe_schedule_next_refresh`, `views._schedule_next_heatmap_refresh` and the beat `kwargs`. Update test_views.py:70. About -25 lines.
- **Risk:** None. If anything outside the repo enqueues `schedule_next=True`, Celery would reject the kwarg, and nothing in the repo does that.

### 3. GitHub client: two HTTP calls and hand-rolled nested validation where one GraphQL `viewer` query works
- **Severity:** medium | **Category:** simplification | **Effort:** M
- **File:** django/main/github_client.py:49-77, 131-178; django/main/heatmap.py:81-86, 39-41
- **Problem:** `fetch_authenticated_user` makes a REST call only to get `login`, then GraphQL is queried by login. The GraphQL response is checked with 7 separate `isinstance(..., Mapping)` steps, each with its own message. heatmap.py then checks `login` (82-86) and day types (39-41) again, although github_client already guarantees both. `except (requests.Timeout, requests.RequestException)` (57, 123) is redundant because Timeout is a subclass. `_graphql_errors_indicate_auth_failure` (16-38) uses 4 separate `if "x" in message` checks.
- **Proposal:** Query `viewer { login contributionsCollection(from:,to:) { contributionCalendar { weeks { contributionDays { date contributionCount } } } } }` in one POST. Wrap `payload["data"]["viewer"]...["weeks"]` in a single `try/except (KeyError, TypeError)` that raises `GitHubUpstreamError`. Use `any(s in message for s in (...))`. Delete `fetch_authenticated_user` and the duplicate checks in heatmap.py. About -70 lines and one fewer network round trip.
- **Risk:** test_heatmap.py mocks two requests and needs rewriting. The error messages become less specific, which only affects logs.

### 4. Server-rendered project grid is hidden behind a fake skeleton until JS runs
- **Severity:** medium | **Category:** frontend | **Effort:** S
- **File:** django/main/templates/projects/index.html:40-62; django/main/static/js/projects-filters.js:88-90
- **Problem:** The cards are already in the HTML, but `#projectGrid` ships with `hidden` and 21 lines of skeleton markup are shown until `DOMContentLoaded`. Without JS, or if JS fails, the grid never appears. The skeleton only adds layout shift.
- **Proposal:** Delete the skeleton block, the `hidden` class on `#projectGrid` and the two toggle lines in the JS. About -25 lines.
- **Risk:** None.

### 5. Heatmap JS: one-element "variants" framework and a dead tooltip mode
- **Severity:** low | **Category:** simplification | **Effort:** M
- **File:** django/main/templates/pages/about.html:260-293, 297-309, 400, 422-424
- **Problem:** `variantConfigs` holds a single config, and every operation then loops `variants.forEach`. The 9-element null filter guards elements that the same template always renders. `tooltipMode === "daisy"` is never true. `heatmapEnabled` is passed into JS only to set a static message that the template could render itself. `day.contribution_count` is never produced by the backend. The JS also recomputes colour levels with its own thresholds (`count < 9`), while the server sends `level` with `<= 9` (heatmap.py:19-29), so the two disagree at count == 9.
- **Proposal:** Use plain `const` element lookups, a `{% if heatmap_enabled %}...{% else %}<p>disabled</p>{% endif %}` in the template, and a `COLORS[day.level]` lookup from the server `level`. Drop the `contribution_count` fallback. About -60 lines.
- **Risk:** Low. Check visually.

### 6. `_calculate_last_30_days_total` defensively re-parses our own payload
- **Severity:** low | **Category:** simplification | **Effort:** S
- **File:** django/main/views.py:200-237
- **Problem:** The function is 38 lines of isinstance, try and continue logic over a payload that `build_weeks_payload` wrote itself (always `{"weeks":[{"days":[{"date": iso, "count": int}]}]}`). It also supports a `contribution_count` key that is never produced.
- **Proposal:** Use `start = date.today() - timedelta(days=29); return sum(d["count"] for w in payload.get("weeks", []) for d in w["days"] if date.fromisoformat(d["date"]) >= start)`. Alternatively, compute it once in `build_weeks_payload` and store it in the payload. About -30 lines.
- **Risk:** An older snapshot written in a different shape would raise an error. Payloads have only ever had one shape.

### 7. Hard-coded `BLOG_REPO_PATHS` dict duplicates `Project.github_url`
- **Severity:** low | **Category:** architecture | **Effort:** M
- **File:** django/main/markdown_sync.py:13-25, 28-41, 58-65, 80-88
- **Problem:** A slug-to-repo-name map for 11 personal repos is kept in code. It exists only for projects without `github_url`, which is already the field that models the repo. Supporting it needs `get_repo_path`, `_active_github_username` (a second profile lookup) and a second pair of candidate URLs.
- **Proposal:** Fill `github_url` for those projects (in admin or with a data migration), then delete the dict, `_active_github_username`, the fallback candidates and the profile-based branch of `build_readme_url`. Change `project_footer.html` to link `project.github_url`. About -40 lines.
- **Risk:** Projects left without `github_url` lose README sync. Check the data first.

### 8. markdown_sync: no-op exception wrapping, a duplicate size check and a hand-rolled dedup
- **Severity:** low | **Category:** simplification | **Effort:** S
- **File:** django/main/markdown_sync.py:90-96, 105-121, 154-155
- **Problem:** `except HTTPError: raise` followed by converting `RequestException` to `OSError` does nothing, because `requests.RequestException` already subclasses `IOError`/`OSError`. The caller's 5-item except tuple reduces to `(OSError, ValueError)`, since `UnicodeDecodeError` is a ValueError. The `Content-Length` pre-check saves nothing: `response.content` is already fully downloaded (no `stream=True`), and the post-check at 123-127 covers the case. The dedup loop is `list(dict.fromkeys(candidates))`.
- **Proposal:** Remove the try/except around `requests.get`, delete lines 112-121, use `dict.fromkeys`, and narrow the caller's except to `(OSError, ValueError)`. About -25 lines.
- **Risk:** None. Behaviour is the same.

### 9. Dead flexibility: unused parameters and redundant `getattr` on settings
- **Severity:** low | **Category:** simplification | **Effort:** S
- **File:** django/main/heatmap.py:15, 68, 111, 121; django/main/github_client.py:83; django/main/markdown_sync.py:99, 135
- **Problem:** No caller or test passes `fetch_heatmap_data(github_token=)`, `is_snapshot_stale(ttl_minutes=)`, `fetch_contribution_days(graphql_url=)` or `sync_project_markdown(timeout=)`. `getattr(settings, "GITHUB_HEATMAP_TOKEN", "")...strip()` and `getattr(settings, "HEATMAP_CACHE_TTL_MINUTES", 60)` re-default and re-strip values that settings.py:172-173 already defines and strips.
- **Proposal:** Delete the parameters and use `settings.X` directly. `get_configured_github_token()` becomes `settings.GITHUB_HEATMAP_TOKEN or None`. About -15 lines.
- **Risk:** None.

### 10. `TaskExecutionStatus` duplicates the latest `TaskExecutionLog` row
- **Severity:** low | **Category:** architecture | **Effort:** M
- **File:** django/main/models.py:118-166; django/main/tasks.py:260-271; django/main/admin.py:63-112
- **Problem:** Both models have the same 9 columns. Every run writes both. Because each run overwrites `last_success_at` and `last_failure_at` with None on the opposite outcome, the status row always equals the newest log row.
- **Proposal:** Drop `TaskExecutionStatus` and read the latest log per task (`TaskExecutionLog.objects.filter(task_name=n).order_by("-last_run_at").first()`). This removes one model, one admin class and half of the task writes.
- **Risk:** Needs a migration and test updates. The log table grows without bound either way, so add pruning if you keep it.

### 11. Settings and config boilerplate: dead or default-valued entries
- **Severity:** low | **Category:** simplification | **Effort:** S
- **File:** django/config/settings.py:24-27, 74, 119-121, 156, 163, 168-170, 181, 207; django/main/apps.py:8, 11-13; django/config/urls.py:1-15
- **Problem:**
  - `STATICFILES_STORAGE` (181) was removed in Django 5.1 and is ignored on 5.1.15.
  - `STATICFILES_DIRS = [main/static]` (156) duplicates what `AppDirectoriesFinder` already collects.
  - `TEMPLATES.DIRS = BASE_DIR/"templates/"` (74) points to a directory that does not exist.
  - `environ.Env(DEBUG=(bool, False))` (24-27) defines a scheme for `DEBUG`, but the code reads `DJANGO_DEBUG`.
  - `AUTHENTICATION_BACKENDS` (168-170) is the Django default.
  - `DEFAULT_AUTO_FIELD` is set both in settings (163) and in `apps.py:8`.
  - Lines 119-121 are commented-out debug prints.
  - `CELERY_RESULT_BACKEND` (207) is unused: every task has `ignore_result=True` and `CELERY_TASK_IGNORE_RESULT=True`, and the views only read `async_result.id`.
  - The startproject docstrings and an `AppConfig.ready()` that only logs DEBUG mode are boilerplate.
- **Proposal:** Delete all of these. Drop the `CELERY_RESULT_BACKEND` env lines from the compose files as well. About -40 lines.
- **Risk:** Removing `STATICFILES_DIRS` changes collectstatic lookup order. The files are identical, so the output is unchanged. Run `make verify`.

### 12. Custom 404/500 handlers re-implement Django defaults
- **Severity:** low | **Category:** simplification | **Effort:** S
- **File:** django/main/views.py:90-97; django/config/urls.py:33-34
- **Problem:** Django's default `page_not_found` and `server_error` already render `404.html` and `500.html` from the template dirs.
- **Proposal:** Rename `errors/404.html` to `404.html` and `errors/500.html` to `500.html`, then delete both handlers and the `handler404`/`handler500` lines. About -12 lines.
- **Risk:** The default 500 handler renders without a request context, so the footer and profile fall back to `|default` values. That is arguably safer, because it avoids 3 DB queries while the site is already erroring.

### 13. Mobile menu JS reimplements the native Popover API
- **Severity:** low | **Category:** frontend | **Effort:** S
- **File:** django/main/static/js/mobile-menu.js:1-39; django/main/templates/base.html:25-47
- **Problem:** About 40 lines of JS handle toggling, `aria-expanded`, Escape-to-close and outside-click-to-close. The `popover` attribute provides all four natively, and daisyUI 5 (package.json) supports popover dropdowns.
- **Proposal:** Use `<button popovertarget="mobile-menu">` and `<ul id="mobile-menu" popover class="dropdown-content ...">`, then delete mobile-menu.js and its `<script>` tag.
- **Risk:** Positioning relies on CSS anchor positioning, which is not supported in older Safari. Test on mobile.

### 14. Projects filter: unnecessary debounce and a JS clear button
- **Severity:** low | **Category:** frontend | **Effort:** S
- **File:** django/main/static/js/projects-filters.js:16-34, 66-71; django/main/templates/projects/index.html:13-28
- **Problem:** Filtering a few dozen DOM nodes is instant, so the two debounce wrappers (about 17 lines) add nothing. `<input type="search">` ships a native clear control and Escape-to-clear.
- **Proposal:** Call `applyFilters` directly on `input`. Optionally switch to `type="search"` and drop `#clearButton` with its handler. About -35 lines.
- **Risk:** Firefox has no visible native clear "x". It still supports Escape. Keep the button if that matters.

### 15. Home timeline duplicates `Project.STATUS_CHOICES`; the card badge hand-maps status labels
- **Severity:** low | **Category:** simplification | **Effort:** S
- **File:** django/main/views.py:103-123; django/main/templates/projects/components/project_card.html:35-41
- **Problem:** `status_labels` and `status_order` repeat `Project.STATUS_CHOICES` (models.py:81-85). The card uses an if/elif chain to print labels that `get_status_display` already provides.
- **Proposal:** Use `[{"status": s, "title": t, "checked": s == "finished", "projects": [p for p in projects if p.status == s]} for s, t in Project.STATUS_CHOICES]`. Use `{{ project.get_status_display }}` in the template, keeping only the colour mapping. About -15 lines.
- **Risk:** None.

### 16. Active-profile lookup repeated 3x; the context processor flattens the model into 15 keys
- **Severity:** low | **Category:** simplification | **Effort:** M
- **File:** django/main/context_processors.py:19-52; django/main/markdown_sync.py:33, 63
- **Problem:** `PortfolioProfile.objects.filter(is_active=True).first() or PortfolioProfile()` is copied in 3 places. The context processor re-exports every field as a `profile_*` key, which mostly renames attributes.
- **Proposal:** Expose `{"profile": source}` and use `{{ profile.full_name }}` in the templates. Keep only the derived `mailto`/`#` fallbacks as template `default` filters. If finding 7 lands, the markdown_sync copies disappear. About -25 lines.
- **Risk:** Touches several templates. Grep `profile_` before renaming.

### 17. Small dead bits in views and templates
- **Severity:** low | **Category:** simplification | **Effort:** S
- **File:** django/main/views.py:134, 340-354, 361, 414; django/main/templates/components/hero_section.html:2-3; django/main/tasks.py:24-26; django/main/urls.py:5-6
- **Problem:**
  - `heatmap_component_visible` is always True (views.py:134 and about.html:47, 257).
  - The `blog_markdown_content` context key is never used in templates.
  - `_load_project_markdown` uses an open/read/finally-close sequence where a `with` block works. It then decodes with `"utf-8"` and strips the BOM separately at 361, where `"utf-8-sig"` would do both.
  - No caller ever passes `hero_section_class` or `hero_inner_class`.
  - Only a test calls `healthcheck_task`.
  - `""` and `"home/"` are two routes with the same name `home`.
- **Proposal:** Delete each of these. Use `with project.markdown_file.open("rb") as f: return f.read().decode("utf-8-sig")`. Make `home/` a `RedirectView` or drop it, and update `VisitorCountMiddleware.is_home` to match. About -30 lines.
- **Risk:** Dropping `/home/` breaks external links to it, so a redirect is the safer choice.

### 18. Admin jobs overview hard-codes schedules that duplicate `CELERY_BEAT_SCHEDULE`
- **Severity:** low | **Category:** simplification | **Effort:** S
- **File:** django/main/views.py:273-286; django/config/settings.py:214-228
- **Problem:** Labels and intervals ("Every 60 minutes", 120) are repeated by hand and will drift from the beat schedule. The disk task is not listed at all. The beat key `sync-project-markdowns-hourly` (settings.py:220) actually runs every 2 hours. Disk-level classification is also duplicated between views.py:240-261 and tasks.py:201-233.
- **Proposal:** Build the list from `settings.CELERY_BEAT_SCHEDULE` and use `entry["schedule"].remaining_estimate(last_run_at)` for the next run. Rename the beat key. Move the disk level into one shared function.
- **Risk:** Low.

### 19. Legacy theme migration in theme-toggle.js
- **Severity:** low | **Category:** frontend | **Effort:** S
- **File:** django/main/static/js/theme-toggle.js:7, 9, 28-30
- **Problem:** The `fantasy2 -> fantasy3` migration is one-time code for an old localStorage value. Side observation, out of lens: the script is `defer` and applies the saved theme on DOMContentLoaded, so `dim2` users see a flash of the light theme on every page load.
- **Proposal:** Delete `legacyThemeMap` and the rewrite branch. An unknown value already falls back to the default. Separately, move the 2-line theme apply into an inline `<head>` script to fix the flash.
- **Risk:** The few users still on `fantasy2` fall back to the default theme, which is the same theme.

---

net: roughly -550 lines possible, -0 deps. Every change uses stdlib or native browser features, or deletes code.

# devkit-core

Scope: full tree of `django/main/views.py`, `tasks.py`, `models.py` and their tests at `4416049` (dev). The probe tests were run in a scratch worktree, which has since been removed.

**Verdict:** CHANGES NEEDED. 4 behavioural findings are confirmed: each test fails on HEAD and passes with the minimal fix. There are also 3 low-severity simplification/library opinions.

Probe test module (scratch only): `django/main/tests/test_audit_probe.py`. Result on HEAD: `FAILED (failures=3, errors=1)`. Result with fixes F1–F4: `OK`.
Gate with the fixes applied: 3 existing tests need adjusting (see Risk).

---

## 1. Admin 500 when adding a tag that differs only in case
- **Severity:** medium · **Category:** bug · **File:** `django/main/models.py:45-49` · **Effort:** S
- **Problem:** `Tag.save()` uppercases `name` after form validation. The ModelForm uniqueness check compares the raw input (`python`) with the stored `PYTHON`, finds no clash and lets it through. `save()` then raises `IntegrityError: UNIQUE constraint failed: main_tag.name`, so the admin returns a 500 instead of a form error.
- **Test (fails on HEAD with IntegrityError):**
  ```python
  Tag.objects.create(name="python")
  self.client.force_login(superuser)
  r = self.client.post(reverse("admin:main_tag_add"), {"name": "python"})
  self.assertEqual(r.status_code, 200); self.assertEqual(Tag.objects.count(), 1)
  ```
- **Proposal (F1, verified):** normalise in `clean()` as well, so that `validate_unique` sees the uppercased value:
  ```python
  def clean(self):
      self.name = self.name.upper()
  ```
- **Risk:** none. Only the admin/ModelForm path changes.

## 2. Media file deleted even when the DB transaction rolls back
- **Severity:** medium · **Category:** bug · **File:** `django/main/models.py:238-262` · **Effort:** S
- **Problem:** `_project_pre_save` and `_project_post_delete` call `storage.delete()` immediately. If the surrounding transaction rolls back (the admin change/delete views run in `atomic`), the row still points to the old `markdown_file`/`thumbnail` but the file is gone. The blog page then silently renders with no content.
- **Test (fails on HEAD: "DB points at a file that was deleted"):**
  ```python
  p.markdown_file.save("old.md", ContentFile(b"old"), save=True); old = p.markdown_file.name
  with self.captureOnCommitCallbacks(execute=True):
      try:
          with transaction.atomic():
              p.markdown_file.save("new.md", ContentFile(b"new"), save=True)
              raise RuntimeError
      except RuntimeError: pass
  p.refresh_from_db(); self.assertTrue(storage.exists(old))
  ```
- **Proposal (F4, verified):** defer the deletion to commit:
  ```python
  name, storage = field.name, field.storage
  transaction.on_commit(lambda: storage.exists(name) and storage.delete(name))
  ```
- **Risk:** `ProjectMediaCleanupTests.test_old_thumbnail_deleted_when_replaced` and `test_thumbnail_deleted_when_project_deleted` must wrap their actions in `self.captureOnCommitCallbacks(execute=True)`.

## 3. Public heatmap endpoint calls GitHub synchronously on every request while the snapshot is stale and the upstream is failing
- **Severity:** medium · **Category:** performance · **File:** `django/main/views.py:157-164` · **Effort:** S
- **Problem:** `update_snapshot_error` (`heatmap.py:159-170`) only writes `last_error` and leaves `fetched_at` unchanged, so the snapshot stays stale. Every anonymous `GET /about/heatmap-data` then makes another blocking GitHub REST + GraphQL round trip until upstream recovers. During a GitHub outage or token expiry, this ties up Gunicorn workers and burns rate limit, even though Celery beat already refreshes the snapshot hourly.
- **Test (fails on HEAD: `5 != 1`):**
  ```python
  HeatmapSnapshot.objects.create(key="portfolio", payload={"weeks": []},
      fetched_at=timezone.now() - timedelta(days=1), ...)
  for _ in range(5): self.client.get(reverse("about_heatmap_data"))
  self.assertEqual(fetch_mock.call_count, 1)   # fetch_mock returns (None, "upstream failure")
  ```
- **Proposal (F, verified):** throttle synchronous refreshes when a payload already exists, for example:
  ```python
  if not snapshot.payload or (is_snapshot_stale(snapshot) and cache.add("heatmap:sync-refresh", 1, 300)):
  ```
  The alternative is to never fetch synchronously when a payload exists and rely on beat.
- **Risk:** the LocMem cache persists across tests, so `ViewsTest` needs `cache.clear()` in `setUp`. Without it, `test_about_heatmap_data_serves_cached_snapshot_when_refresh_fails` fails. Production must have a shared cache backend for the throttle to apply across workers; LocMem works per process.

## 4. Admin "next run" time does not match the beat schedule
- **Severity:** low · **Category:** bug · **File:** `django/main/views.py:273-296` · **Effort:** S
- **Problem:** `next_run_at` is calculated as `last_run_at + interval`. Beat uses `crontab(minute=0)` and `crontab(hour="*/2", minute=0)` (`config/settings.py` `CELERY_BEAT_SCHEDULE`). A manual run at :30 therefore shows the next run at :30 when it is really at :00. A stale `last_run_at` gives a next-run time in the past. The intervals are a second hard-coded copy of the beat schedule, and `check_disk_usage_task` is missing from the overview.
- **Test (fails on HEAD: `30 != 0`):**
  ```python
  last = timezone.now().replace(minute=30, second=0, microsecond=0) - timedelta(hours=2)
  TaskExecutionStatus.objects.create(task_name=REFRESH_HEATMAP_TASK_NAME, last_run_at=last)
  job = [j for j in _get_scheduled_jobs_overview() if j["task_name"] == REFRESH_HEATMAP_TASK_NAME][0]
  self.assertEqual(job["next_run_at"].minute, 0); self.assertGreater(job["next_run_at"], timezone.now())
  ```
- **Proposal (F, verified):** derive the next run from `settings.CELERY_BEAT_SCHEDULE[...]["schedule"].remaining_estimate(now)` and drop `interval_minutes`/`schedule_label` duplication.
- **Risk:** minimal. The change is display only.

---

## Opinions (low, not behavioural)

## 5. Dead `schedule_next` chaining and an unused helper
- **Severity:** low · **Category:** simplification · **File:** `django/main/views.py:189-197`, `django/main/tasks.py:113,142,168,192,250-257` · **Effort:** S
- **Problem:** `_schedule_next_heatmap_refresh` is never called (grep shows no other reference). `schedule_next` is `False` at every call site (beat kwargs in `settings.py`, `views.py:452`), so `_maybe_schedule_next_refresh` never enqueues anything. If it were enabled, it would also double-schedule alongside beat.
- **Proposal:** delete the helper, the `schedule_next` parameter and `_maybe_schedule_next_refresh`, then update the beat kwargs and tests.
- **Risk:** in-flight queued messages carrying `schedule_next` kwargs would fail on deploy. Keep `**kwargs` for one release, or drain the queue first.

## 6. Duplicated status-recording blocks in tasks
- **Severity:** low · **Category:** simplification · **File:** `django/main/tasks.py:63-101,119-191,206-247` · **Effort:** S
- **Problem:** the same `status.last_* = ...; status.save(update_fields=[8 fields]); _log_task_execution(status)` block appears 5 times. The "not configured" branch (`tasks.py:119-143`) does the same thing as the error branch, because `fetch_heatmap_data()` already returns `(None, "Heatmap is not configured.")` when no token is set (`heatmap.py:76-77`). `failed_results`/`last_error` is also computed twice (`tasks.py:76-89`).
- **Proposal:** add one `_record(status, outcome, total, updated, failed, error="")` helper and drop the redundant token pre-check. This removes roughly 100 lines.
- **Risk:** low. `test_tasks.py` covers each branch.

## 7. `bleach` is deprecated upstream
- **Severity:** low · **Category:** library · **File:** `django/main/views.py:1,371-377` · **Effort:** M
- **Problem:** the markdown sanitiser depends on `bleach==6.2.0`. Mozilla deprecated bleach in January 2023 and it gets security fixes only.
- **Proposal:** plan a migration to `nh3`, which supports tag/attribute allowlists and an `attribute_filter` callback that can replace `_clean_attributes`. Keep the existing sanitize tests in `test_views.py` as the gate.
- **Risk:** small differences in the sanitiser output. The existing XSS tests cover the main cases.

Refuted: 0 · Filtered: 3 (`last_success_at` reset on failure is pinned by tests as intended, the markdown file rename on each sync is in markdown_sync scope, and `div/span class` passthrough comes from trusted README input) · Gate: not run on HEAD (probe only)

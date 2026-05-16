# Codebase Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix security issues, dead code, disk resource waste, and outdated dependencies identified in the codebase audit, plus add disk usage monitoring for the admin panel.

**Architecture:** One branch (`audit/codebase-2026`), four categories as separate commits. No new models or migrations — disk monitoring reuses `TaskExecutionStatus`. Requests replaces urllib in markdown sync; bleach gets a custom attribute cleaner for img src.

**Tech Stack:** Django 5.1, Celery, bleach, requests, shutil, Docker Compose, PostgreSQL, uv

---

## File Map

| File | Change |
|---|---|
| `django/config/celery.py` | Remove `debug_task` |
| `django/config/settings.py` | Add `CELERY_TASK_IGNORE_RESULT`, remove whitenoise comment, add disk task to beat schedule |
| `django/main/tasks.py` | Add `ignore_result=True` to `healthcheck_task`, add `check_disk_usage_task` |
| `django/main/context_processors.py` | Fix `visitor_counter` — replace `get_instance()` with read-only query |
| `django/main/markdown_sync.py` | Replace urllib with requests; remove `opener` param |
| `django/main/models.py` | Add `post_delete`/`pre_save` signals on `Project` for media file cleanup |
| `django/main/views.py` | Add `_clean_attributes` for img src filtering; update `bleach.clean()` call; add `_get_disk_info()`; pass `disk_info` to about context |
| `django/main/templates/pages/about.html` | Add Disk Usage admin panel section |
| `infra/Dockerfile` | `node:20-slim` → `node:22-slim` |
| `infra/docker-compose.prod.yml` | `postgres:13` → `postgres:16` |
| `.env.example` | Add `DJANGO_DEBUG` production warning comment |
| `uv.lock` | Updated by `uv lock --upgrade-package` |
| `django/main/tests/test_markdown_sync.py` | Update from opener-pattern to `patch('main.markdown_sync.requests.get', ...)` |
| `django/main/tests/test_tasks.py` | Add test for `check_disk_usage_task` |
| `django/main/tests/test_views.py` | Add tests for img src filter and disk panel |
| `django/main/tests/test_models.py` | Add test for post_delete media cleanup |

---

## Task 1: Remove dead code — `debug_task` and whitenoise comment

**Files:**
- Modify: `django/config/celery.py`
- Modify: `django/config/settings.py`

- [ ] **Step 1: Delete `debug_task` from celery.py**

  Open `django/config/celery.py`. The file currently ends with:
  ```python
  @app.task(bind=True)
  def debug_task(self):
      print(f"Request: {self.request!r}")
  ```
  Delete those four lines entirely. The file should now end at `app.autodiscover_tasks()`.

- [ ] **Step 2: Remove commented whitenoise line from settings.py**

  Open `django/config/settings.py`. Find and delete line 181:
  ```python
  # STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # Commented out as we're using Caddy for static files
  ```
  The active `STATICFILES_STORAGE` line on 182 stays untouched.

- [ ] **Step 3: Verify**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 uv run python django/manage.py check
  grep -r "debug_task\|whitenoise" django/config/
  ```
  Expected: `System check identified no issues`. The grep returns no matches.

- [ ] **Step 4: Commit**

  ```bash
  git add django/config/celery.py django/config/settings.py
  git commit -m "chore: remove debug_task dead code and whitenoise dead comment"
  ```

---

## Task 2: Disable Celery result backend writes

**Files:**
- Modify: `django/config/settings.py`
- Modify: `django/main/tasks.py`

- [ ] **Step 1: Write failing test**

  Open `django/main/tests/test_tasks.py`. Add this import at the top alongside existing ones:
  ```python
  from main.tasks import healthcheck_task, DISK_USAGE_TASK_NAME
  ```
  Add this test class at the end of the file:
  ```python
  class TaskIgnoreResultTests(TestCase):
      def test_healthcheck_task_has_ignore_result(self):
          self.assertTrue(getattr(healthcheck_task, "ignore_result", False))
  ```

- [ ] **Step 2: Run it to verify it fails**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_tasks.TaskIgnoreResultTests -v 2
  ```
  Expected: FAIL — `AssertionError: False is not true`

- [ ] **Step 3: Add `CELERY_TASK_IGNORE_RESULT` to settings**

  Open `django/config/settings.py`. Find the Celery block (starts with `CELERY_BROKER_URL`). Add one line directly after `CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True`:
  ```python
  CELERY_TASK_IGNORE_RESULT = True
  ```

- [ ] **Step 4: Add `ignore_result=True` to `healthcheck_task`**

  Open `django/main/tasks.py`. Find:
  ```python
  @shared_task
  def healthcheck_task():
      return "ok"
  ```
  Replace with:
  ```python
  @shared_task(ignore_result=True)
  def healthcheck_task():
      return "ok"
  ```

- [ ] **Step 5: Run test to verify it passes**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_tasks.TaskIgnoreResultTests -v 2
  ```
  Expected: PASS

- [ ] **Step 6: Commit**

  ```bash
  git add django/config/settings.py django/main/tasks.py django/main/tests/test_tasks.py
  git commit -m "perf: disable celery result backend writes — results are never read"
  ```

---

## Task 3: Fix `visitor_counter` context processor

**Files:**
- Modify: `django/main/context_processors.py`
- Test: `django/main/tests/test_views.py` (run existing, no new test needed)

- [ ] **Step 1: Run existing context processor tests first**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_views -v 2
  ```
  Note which tests pass — all must pass after the change too.

- [ ] **Step 2: Replace `visitor_counter` with read-only query**

  Open `django/main/context_processors.py`. Find:
  ```python
  def visitor_counter(request):
      """Expose the global visit counter to all templates.

      Returns:
          dict: Context with `visitor_count` key.
      """
      count = PageView.get_instance().count
      return {"visitor_count": count}
  ```
  Replace with:
  ```python
  def visitor_counter(request):
      instance = PageView.objects.filter(id=1).first()
      return {"visitor_count": instance.count if instance else 0}
  ```

- [ ] **Step 3: Run tests to verify nothing broke**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_views -v 2
  ```
  Expected: same tests pass as before.

- [ ] **Step 4: Commit**

  ```bash
  git add django/main/context_processors.py
  git commit -m "refactor: replace get_or_create with read-only query in visitor_counter"
  ```

---

## Task 4: Migrate `markdown_sync` from urllib to requests

**Files:**
- Modify: `django/main/markdown_sync.py`
- Modify: `django/main/tests/test_markdown_sync.py`

- [ ] **Step 1: Run existing markdown sync tests first to confirm baseline**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_markdown_sync -v 2
  ```
  All tests must pass before touching code.

- [ ] **Step 2: Rewrite `_download_markdown` and remove urllib in `markdown_sync.py`**

  Open `django/main/markdown_sync.py`. Replace the import block at the top:
  ```python
  # OLD — remove these three lines:
  from urllib.error import HTTPError, URLError
  from urllib.request import Request, urlopen
  ```
  Keep `from urllib.parse import urlparse` (still used by `_active_github_username` and `_parse_github_owner_repo`).

  Add `import requests` after `import logging`.

  The file's imports section should now read:
  ```python
  import logging
  import requests
  from pathlib import Path
  from urllib.parse import urlparse

  from django.core.files.base import ContentFile

  from .models import PortfolioProfile
  ```

  Replace the entire `_download_markdown` function:
  ```python
  def _download_markdown(url, timeout=20):
      try:
          response = requests.get(
              url,
              headers={"User-Agent": "my-django-portfolio-markdown-sync/1.0"},
              timeout=timeout,
          )
          response.raise_for_status()
      except requests.exceptions.HTTPError as exc:
          raise exc
      except requests.exceptions.RequestException as exc:
          raise OSError(str(exc)) from exc

      content_length = response.headers.get("Content-Length")
      if content_length is not None:
          try:
              parsed_length = int(content_length)
          except (TypeError, ValueError):
              parsed_length = None
          if parsed_length is not None and parsed_length > MAX_MARKDOWN_SIZE_BYTES:
              raise ValueError(
                  f"Downloaded markdown exceeds size limit ({MAX_MARKDOWN_SIZE_BYTES} bytes)"
              )

      raw_bytes = response.content
      if len(raw_bytes) > MAX_MARKDOWN_SIZE_BYTES:
          raise ValueError(
              f"Downloaded markdown exceeds size limit ({MAX_MARKDOWN_SIZE_BYTES} bytes)"
          )

      text = raw_bytes.decode("utf-8-sig")
      if text.lstrip().lower().startswith("<!doctype html") or text.lstrip().lower().startswith("<html"):
          raise ValueError("Downloaded content is HTML, expected Markdown")
      return text
  ```

  Update `sync_project_markdown` signature — remove the `opener=urlopen` parameter. Change:
  ```python
  def sync_project_markdown(project, timeout=20, opener=urlopen):
  ```
  to:
  ```python
  def sync_project_markdown(project, timeout=20):
  ```

  Inside `sync_project_markdown`, change the call from:
  ```python
  markdown_text = _download_markdown(url, timeout=timeout, opener=opener)
  ```
  to:
  ```python
  markdown_text = _download_markdown(url, timeout=timeout)
  ```

  Change the `except` clause inside the `for url in candidate_urls` loop from:
  ```python
  except (HTTPError, URLError, UnicodeDecodeError, ValueError, OSError) as exc:
  ```
  to:
  ```python
  except (requests.exceptions.HTTPError, requests.exceptions.RequestException,
          UnicodeDecodeError, ValueError, OSError) as exc:
  ```

- [ ] **Step 3: Update `test_markdown_sync.py` to use `requests.get` mocking**

  Open `django/main/tests/test_markdown_sync.py`. Replace the entire file content:

  ```python
  import datetime
  import shutil
  import tempfile
  from unittest.mock import MagicMock, patch

  import requests

  from django.core.files.base import ContentFile
  from django.test import TestCase, override_settings

  from main.markdown_sync import sync_project_markdown
  from main.models import PortfolioProfile, Project


  def _make_mock_response(content: bytes, status_code: int = 200) -> MagicMock:
      resp = MagicMock()
      resp.status_code = status_code
      resp.content = content
      resp.headers = {}
      if status_code >= 400:
          resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
              response=resp
          )
      else:
          resp.raise_for_status.return_value = None
      return resp


  class MarkdownSyncTests(TestCase):
      @classmethod
      def setUpClass(cls):
          super().setUpClass()
          cls._media_root = tempfile.mkdtemp(prefix="markdown-sync-tests-")
          cls._override = override_settings(MEDIA_ROOT=cls._media_root)
          cls._override.enable()

      @classmethod
      def tearDownClass(cls):
          cls._override.disable()
          shutil.rmtree(cls._media_root, ignore_errors=True)
          super().tearDownClass()

      def setUp(self):
          profile = PortfolioProfile.objects.get(is_active=True)
          profile.github_url = "https://github.com/test-user"
          profile.save(update_fields=["github_url"])

      def test_sync_project_markdown_replaces_file_on_success(self):
          project = Project.objects.create(
              title="Sync Success",
              short_description="sync test",
              date=datetime.date(2025, 1, 1),
              blog=True,
              blog_url="sync-success",
              github_url="https://github.com/example/sync-success",
              status="finished",
          )
          project.markdown_file.save("sync-success.md", ContentFile(b"# Old"), save=True)

          with patch(
              "main.markdown_sync.requests.get",
              return_value=_make_mock_response(b"# New Content\n\nUpdated."),
          ):
              result = sync_project_markdown(project)

          self.assertTrue(result["updated"])
          project.refresh_from_db()
          project.markdown_file.open("rb")
          self.assertEqual(
              project.markdown_file.read().decode("utf-8"), "# New Content\n\nUpdated."
          )
          project.markdown_file.close()

      def test_sync_project_markdown_keeps_old_file_on_failure(self):
          project = Project.objects.create(
              title="Sync Failure",
              short_description="sync test",
              date=datetime.date(2025, 1, 1),
              blog=True,
              blog_url="sync-failure",
              github_url="https://github.com/example/sync-failure",
              status="finished",
          )
          project.markdown_file.save("sync-failure.md", ContentFile(b"# Old"), save=True)
          old_name = project.markdown_file.name

          with patch(
              "main.markdown_sync.requests.get",
              side_effect=requests.exceptions.ConnectionError("network down"),
          ):
              result = sync_project_markdown(project)

          self.assertFalse(result["updated"])
          project.refresh_from_db()
          self.assertEqual(project.markdown_file.name, old_name)
          project.markdown_file.open("rb")
          self.assertEqual(project.markdown_file.read().decode("utf-8"), "# Old")
          project.markdown_file.close()

      def test_sync_project_markdown_rejects_oversized_download(self):
          project = Project.objects.create(
              title="Sync Too Large",
              short_description="sync test",
              date=datetime.date(2025, 1, 1),
              blog=True,
              blog_url="sync-too-large",
              github_url="https://github.com/example/sync-too-large",
              status="finished",
          )
          project.markdown_file.save("sync-too-large.md", ContentFile(b"# Old"), save=True)
          old_name = project.markdown_file.name
          oversized_payload = b"a" * (10 * 1024 * 1024 + 1)

          with patch(
              "main.markdown_sync.requests.get",
              return_value=_make_mock_response(oversized_payload),
          ):
              result = sync_project_markdown(project)

          self.assertFalse(result["updated"])
          self.assertEqual(result["reason"], "download_failed")
          self.assertIn("exceeds size limit", result["error"])

          project.refresh_from_db()
          self.assertEqual(project.markdown_file.name, old_name)
          project.markdown_file.open("rb")
          self.assertEqual(project.markdown_file.read().decode("utf-8"), "# Old")
          project.markdown_file.close()
  ```

- [ ] **Step 4: Run updated tests to verify they pass**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_markdown_sync -v 2
  ```
  Expected: all three tests PASS.

- [ ] **Step 5: Verify no urllib imports remain in markdown_sync**

  ```bash
  grep "urllib.request\|urllib.error\|urlopen\|HTTPError\|URLError" django/main/markdown_sync.py
  ```
  Expected: no output.

- [ ] **Step 6: Commit**

  ```bash
  git add django/main/markdown_sync.py django/main/tests/test_markdown_sync.py
  git commit -m "refactor: migrate markdown_sync HTTP client from urllib to requests"
  ```

---

## Task 5: Auto-delete media files when Project is deleted or field cleared

**Files:**
- Modify: `django/main/models.py`
- Test: `django/main/tests/test_models.py`

- [ ] **Step 1: Write failing tests**

  Open `django/main/tests/test_models.py`. Add these imports at the top if not present:
  ```python
  import datetime
  import shutil
  import tempfile
  from django.core.files.base import ContentFile
  from django.test import TestCase, override_settings
  ```

  Add this test class at the end of the file:
  ```python
  class ProjectMediaCleanupTests(TestCase):
      @classmethod
      def setUpClass(cls):
          super().setUpClass()
          cls._media_root = tempfile.mkdtemp(prefix="project-media-tests-")
          cls._override = override_settings(MEDIA_ROOT=cls._media_root)
          cls._override.enable()

      @classmethod
      def tearDownClass(cls):
          cls._override.disable()
          shutil.rmtree(cls._media_root, ignore_errors=True)
          super().tearDownClass()

      def _make_project_with_thumbnail(self):
          from main.models import Project
          project = Project.objects.create(
              title="Media Test",
              short_description="test",
              date=datetime.date(2025, 1, 1),
              status="finished",
          )
          project.thumbnail.save("thumb.png", ContentFile(b"fake-png"), save=True)
          return project

      def test_thumbnail_deleted_when_project_deleted(self):
          from main.models import Project
          project = self._make_project_with_thumbnail()
          storage = project.thumbnail.storage
          thumb_name = project.thumbnail.name
          self.assertTrue(storage.exists(thumb_name))

          project.delete()

          self.assertFalse(storage.exists(thumb_name))

      def test_old_thumbnail_deleted_when_replaced(self):
          from main.models import Project
          project = self._make_project_with_thumbnail()
          storage = project.thumbnail.storage
          old_name = project.thumbnail.name
          self.assertTrue(storage.exists(old_name))

          project.thumbnail.save("thumb_new.png", ContentFile(b"new-fake-png"), save=True)

          self.assertFalse(storage.exists(old_name))
  ```

- [ ] **Step 2: Run to verify tests fail**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_models.ProjectMediaCleanupTests -v 2
  ```
  Expected: FAIL — the files still exist after delete/replace.

- [ ] **Step 3: Add signal handlers to `models.py`**

  Open `django/main/models.py`. Add this import at the top:
  ```python
  from django.db.models.signals import post_delete, pre_save
  from django.dispatch import receiver
  ```

  Add these signal handlers at the end of the file (after all model definitions):
  ```python
  def _delete_file_field(field):
      """Delete the file associated with a FileField/ImageField if it exists."""
      if field and field.name:
          storage = field.storage
          if storage.exists(field.name):
              storage.delete(field.name)


  @receiver(post_delete, sender=Project)
  def _project_post_delete(sender, instance, **kwargs):
      _delete_file_field(instance.thumbnail)
      _delete_file_field(instance.markdown_file)


  @receiver(pre_save, sender=Project)
  def _project_pre_save(sender, instance, **kwargs):
      if not instance.pk:
          return
      try:
          old = Project.objects.get(pk=instance.pk)
      except Project.DoesNotExist:
          return
      if old.thumbnail and old.thumbnail != instance.thumbnail:
          _delete_file_field(old.thumbnail)
      if old.markdown_file and old.markdown_file != instance.markdown_file:
          _delete_file_field(old.markdown_file)
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_models.ProjectMediaCleanupTests -v 2
  ```
  Expected: PASS.

- [ ] **Step 5: Run full suite to confirm no regression**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main -v 2
  ```
  Expected: all tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add django/main/models.py django/main/tests/test_models.py
  git commit -m "feat: auto-delete media files when Project is deleted or thumbnail replaced"
  ```

---

## Task 6: Restrict `img src` in markdown rendering to GitHub domains

**Files:**
- Modify: `django/main/views.py`
- Test: `django/main/tests/test_views.py`

- [ ] **Step 1: Write failing test**

  Open `django/main/tests/test_views.py`. Find the `ViewsTest` class. Add this test method to it:
  ```python
  def test_blog_detail_strips_external_img_src(self):
      import shutil, tempfile
      from django.core.files.base import ContentFile
      from django.test import override_settings

      media_root = tempfile.mkdtemp(prefix="blog-img-test-")
      try:
          with override_settings(MEDIA_ROOT=media_root):
              project = Project.objects.create(
                  title="Img Test",
                  short_description="img",
                  date=datetime.date(2024, 1, 1),
                  blog=True,
                  blog_url="img-test-slug",
                  status="finished",
              )
              external_md = b'# Test\n\n![tracker](https://evil.com/pixel.gif)\n\n![github](https://raw.githubusercontent.com/user/repo/main/img.png)\n'
              project.markdown_file.save("img-test-slug.md", ContentFile(external_md), save=True)

              response = self.client.get(reverse("blog_detail", args=["img-test-slug"]))

              self.assertEqual(response.status_code, 200)
              content = response.content.decode()
              self.assertNotIn("evil.com", content)
              self.assertIn("raw.githubusercontent.com", content)
      finally:
          shutil.rmtree(media_root, ignore_errors=True)
  ```

- [ ] **Step 2: Run to verify it fails**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_views.ViewsTest.test_blog_detail_strips_external_img_src -v 2
  ```
  Expected: FAIL — `evil.com` appears in rendered content.

- [ ] **Step 3: Add `_clean_attributes` and update `bleach.clean()` in `views.py`**

  Open `django/main/views.py`. Find the constants block near the top (after imports). After `ALLOWED_MARKDOWN_PROTOCOLS`, add:

  ```python
  _GITHUB_IMG_PREFIXES = (
      "https://github.com/",
      "https://raw.githubusercontent.com/",
      "https://camo.githubusercontent.com/",
  )


  def _clean_attributes(tag, name, value):
      if tag == "img" and name == "src":
          return any(value.startswith(p) for p in _GITHUB_IMG_PREFIXES)
      return True
  ```

  Now find the `blog_detail` view. Inside it, find the `bleach.clean()` call. It currently looks like:
  ```python
  bleach.clean(
      html_content,
      tags=ALLOWED_MARKDOWN_TAGS,
      attributes=ALLOWED_MARKDOWN_ATTRIBUTES,
      protocols=ALLOWED_MARKDOWN_PROTOCOLS,
      strip=True,
  )
  ```
  Change `attributes=ALLOWED_MARKDOWN_ATTRIBUTES` to `attributes=_clean_attributes`:
  ```python
  bleach.clean(
      html_content,
      tags=ALLOWED_MARKDOWN_TAGS,
      attributes=_clean_attributes,
      protocols=ALLOWED_MARKDOWN_PROTOCOLS,
      strip=True,
  )
  ```

- [ ] **Step 4: Run the test to verify it passes**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_views.ViewsTest.test_blog_detail_strips_external_img_src -v 2
  ```
  Expected: PASS.

- [ ] **Step 5: Run full view tests**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_views -v 2
  ```
  Expected: all tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add django/main/views.py django/main/tests/test_views.py
  git commit -m "security: restrict img src in markdown to github.com domains only"
  ```

---

## Task 7: Add `.env.example` production warning

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Add warning comment to `DJANGO_DEBUG` line**

  Open `.env.example`. Find:
  ```
  DJANGO_DEBUG=True
  ```
  Replace with:
  ```
  DJANGO_DEBUG=True  # DEVELOPMENT ONLY — set to False in production
  ```

- [ ] **Step 2: Verify**

  ```bash
  grep "DJANGO_DEBUG" .env.example
  ```
  Expected: `DJANGO_DEBUG=True  # DEVELOPMENT ONLY — set to False in production`

- [ ] **Step 3: Commit**

  ```bash
  git add .env.example
  git commit -m "docs: warn against copying DJANGO_DEBUG=True to production"
  ```

---

## Task 8: Disk usage monitoring Celery task

**Files:**
- Modify: `django/main/tasks.py`
- Modify: `django/config/settings.py`
- Test: `django/main/tests/test_tasks.py`

- [ ] **Step 1: Write failing test**

  Open `django/main/tests/test_tasks.py`. Add this import at the top:
  ```python
  import shutil
  from unittest.mock import patch
  from main.tasks import check_disk_usage_task, DISK_USAGE_TASK_NAME
  ```

  Add this test class at the end of the file:
  ```python
  class DiskUsageTaskTests(TestCase):
      def _make_usage(self, total_gb, used_gb):
          total = int(total_gb * 1024 ** 3)
          used = int(used_gb * 1024 ** 3)
          free = total - used
          return shutil.disk_usage.__class__.__mro__  # placeholder — see below
  ```

  Actually replace the entire class with:
  ```python
  class DiskUsageTaskTests(TestCase):
      def _fake_usage(self, total_gb, free_gb):
          total = int(total_gb * 1024 ** 3)
          free = int(free_gb * 1024 ** 3)
          used = total - free
          import collections
          DiskUsage = collections.namedtuple("DiskUsage", ["total", "used", "free"])
          return DiskUsage(total=total, used=used, free=free)

      def test_disk_task_success_when_ample_space(self):
          usage = self._fake_usage(total_gb=10.0, free_gb=5.0)
          with patch("main.tasks.shutil.disk_usage", return_value=usage):
              check_disk_usage_task()

          status = TaskExecutionStatus.objects.get(task_name=DISK_USAGE_TASK_NAME)
          self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_SUCCESS)
          self.assertEqual(status.last_error, "")

      def test_disk_task_partial_when_below_2gb(self):
          usage = self._fake_usage(total_gb=10.0, free_gb=1.5)
          with patch("main.tasks.shutil.disk_usage", return_value=usage):
              check_disk_usage_task()

          status = TaskExecutionStatus.objects.get(task_name=DISK_USAGE_TASK_NAME)
          self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_PARTIAL_SUCCESS)
          self.assertIn("1.5", status.last_error)

      def test_disk_task_failure_when_below_1gb(self):
          usage = self._fake_usage(total_gb=10.0, free_gb=0.8)
          with patch("main.tasks.shutil.disk_usage", return_value=usage):
              check_disk_usage_task()

          status = TaskExecutionStatus.objects.get(task_name=DISK_USAGE_TASK_NAME)
          self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_FAILURE)
          self.assertIn("CRITICAL", status.last_error)
  ```

- [ ] **Step 2: Run to verify they fail**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_tasks.DiskUsageTaskTests -v 2
  ```
  Expected: ImportError or AttributeError — `check_disk_usage_task` doesn't exist yet.

- [ ] **Step 3: Add `check_disk_usage_task` to `tasks.py`**

  Open `django/main/tasks.py`. Add `import shutil` to the imports at the top.

  Add the constant after the existing task name constants:
  ```python
  DISK_USAGE_TASK_NAME = "main.check_disk_usage_task"
  ```

  Add the task function after the existing task functions (before `_maybe_schedule_next_refresh`):
  ```python
  @shared_task(ignore_result=True)
  def check_disk_usage_task():
      usage = shutil.disk_usage("/")
      free_gb = usage.free / (1024 ** 3)

      status, _ = TaskExecutionStatus.objects.get_or_create(task_name=DISK_USAGE_TASK_NAME)
      status.last_run_at = timezone.now()
      status.last_total = 1

      if free_gb < 1.0:
          logger.critical("DISK CRITICAL: only %.1f GB free on /", free_gb)
          status.last_status = TaskExecutionStatus.STATUS_FAILURE
          status.last_updated = 0
          status.last_failed = 1
          status.last_error = f"CRITICAL: {free_gb:.1f} GB free (below 1 GB threshold)"
          status.last_success_at = None
          status.last_failure_at = timezone.now()
      elif free_gb < 2.0:
          logger.warning("DISK WARNING: only %.1f GB free on /", free_gb)
          status.last_status = TaskExecutionStatus.STATUS_PARTIAL_SUCCESS
          status.last_updated = 0
          status.last_failed = 1
          status.last_error = f"WARNING: {free_gb:.1f} GB free (below 2 GB threshold)"
          status.last_success_at = None
          status.last_failure_at = timezone.now()
      else:
          logger.info("DISK OK: %.1f GB free on /", free_gb)
          status.last_status = TaskExecutionStatus.STATUS_SUCCESS
          status.last_updated = 1
          status.last_failed = 0
          status.last_error = ""
          status.last_success_at = timezone.now()
          status.last_failure_at = None

      status.save(
          update_fields=[
              "last_status",
              "last_run_at",
              "last_success_at",
              "last_failure_at",
              "last_total",
              "last_updated",
              "last_failed",
              "last_error",
          ]
      )
      _log_task_execution(status)
  ```

- [ ] **Step 4: Register task in beat schedule**

  Open `django/config/settings.py`. Find `CELERY_BEAT_SCHEDULE`. Add a new entry:
  ```python
  "check-disk-usage-daily": {
      "task": "main.tasks.check_disk_usage_task",
      "schedule": crontab(hour=6, minute=0),
  },
  ```

- [ ] **Step 5: Run tests to verify they pass**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_tasks.DiskUsageTaskTests -v 2
  ```
  Expected: all three PASS.

- [ ] **Step 6: Commit**

  ```bash
  git add django/main/tasks.py django/config/settings.py django/main/tests/test_tasks.py
  git commit -m "feat: add daily disk usage monitoring task with warning/critical thresholds"
  ```

---

## Task 9: Disk usage panel on admin about page

**Files:**
- Modify: `django/main/views.py`
- Modify: `django/main/templates/pages/about.html`
- Test: `django/main/tests/test_views.py`

- [ ] **Step 1: Write failing test**

  Open `django/main/tests/test_views.py`. Find the `ViewsTest` class. Add:
  ```python
  def test_about_shows_disk_info_for_staff(self):
      from django.contrib.auth import get_user_model
      User = get_user_model()
      staff = User.objects.create_user("diskstaff", password="pass", is_staff=True)
      self.client.force_login(staff)

      response = self.client.get(reverse("about"))

      self.assertEqual(response.status_code, 200)
      self.assertIn("disk_info", response.context)
      disk = response.context["disk_info"]
      self.assertIn("free_gb", disk)
      self.assertIn("used_gb", disk)
      self.assertIn("total_gb", disk)
      self.assertIn("level", disk)
      self.assertIn(disk["level"], ("ok", "warning", "critical"))
  ```

- [ ] **Step 2: Run to verify it fails**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_views.ViewsTest.test_about_shows_disk_info_for_staff -v 2
  ```
  Expected: FAIL — `disk_info` not in context.

- [ ] **Step 3: Add `_get_disk_info()` helper and inject into about view**

  Open `django/main/views.py`. Add `import shutil` to the imports at the top.

  Add this helper function near the other private helpers (`_get_scheduled_jobs_overview`, `_get_executed_tasks`):
  ```python
  def _get_disk_info():
      usage = shutil.disk_usage("/")
      free_gb = round(usage.free / (1024 ** 3), 1)
      used_gb = round(usage.used / (1024 ** 3), 1)
      total_gb = round(usage.total / (1024 ** 3), 1)
      free_pct = round((usage.free / usage.total) * 100, 1)

      if free_gb < 1.0:
          level = "critical"
      elif free_gb < 2.0:
          level = "warning"
      else:
          level = "ok"

      return {
          "free_gb": free_gb,
          "used_gb": used_gb,
          "total_gb": total_gb,
          "free_pct": free_pct,
          "level": level,
      }
  ```

  In the `about` view, find the `if is_admin_user:` block:
  ```python
  if is_admin_user:
      context["scheduled_jobs"] = _get_scheduled_jobs_overview()
      context["executed_tasks"] = _get_executed_tasks()
  ```
  Add one line:
  ```python
  if is_admin_user:
      context["scheduled_jobs"] = _get_scheduled_jobs_overview()
      context["executed_tasks"] = _get_executed_tasks()
      context["disk_info"] = _get_disk_info()
  ```

- [ ] **Step 4: Run test to verify it passes**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_views.ViewsTest.test_about_shows_disk_info_for_staff -v 2
  ```
  Expected: PASS.

- [ ] **Step 5: Add Disk Usage panel to `about.html`**

  Open `django/main/templates/pages/about.html`. Find the line:
  ```html
  {% if request.user.is_authenticated and request.user.is_staff %}
  <section class="mt-6 rounded-2xl border border-base-300 bg-base-200 shadow-sm">
      <div class="p-4 sm:p-6">
          <div class="flex items-center justify-between">
              <h2 class="text-xl font-semibold text-primary">Scheduled Jobs</h2>
  ```

  Insert the following block **before** that `{% if %}` tag (so it appears before the Scheduled Jobs section, still inside the admin guard — move it inside the existing admin `{% if %}` block):

  Actually, the disk panel goes **inside** the existing `{% if request.user.is_authenticated and request.user.is_staff %}` block, **before** the Scheduled Jobs section. Find:
  ```html
      {% if request.user.is_authenticated and request.user.is_staff %}
      <section class="mt-6 rounded-2xl border border-base-300 bg-base-200 shadow-sm">
          <div class="p-4 sm:p-6">
              <div class="flex items-center justify-between">
                  <h2 class="text-xl font-semibold text-primary">Scheduled Jobs</h2>
  ```

  Insert this block between the `{% if request.user.is_authenticated and request.user.is_staff %}` line and the Scheduled Jobs `<section>`:
  ```html
      {% if disk_info %}
      <section class="mt-6 rounded-2xl border border-base-300 bg-base-200 shadow-sm">
          <div class="p-4 sm:p-6">
              <div class="flex items-center justify-between">
                  <h2 class="text-xl font-semibold text-primary">Disk Usage</h2>
                  <span class="badge badge-outline badge-sm">Admin</span>
              </div>
              <div class="mt-4 grid gap-3 sm:grid-cols-3">
                  <article class="rounded-xl border border-base-300 bg-base-100 p-4">
                      <p class="text-xs font-medium uppercase tracking-wide text-base-content/80">Free</p>
                      <p class="mt-1 text-lg font-semibold {% if disk_info.level == 'critical' %}text-error{% elif disk_info.level == 'warning' %}text-warning{% else %}text-success{% endif %}">
                          {{ disk_info.free_gb }} GB ({{ disk_info.free_pct }}%)
                      </p>
                  </article>
                  <article class="rounded-xl border border-base-300 bg-base-100 p-4">
                      <p class="text-xs font-medium uppercase tracking-wide text-base-content/80">Used</p>
                      <p class="mt-1 text-lg font-semibold">{{ disk_info.used_gb }} GB</p>
                  </article>
                  <article class="rounded-xl border border-base-300 bg-base-100 p-4">
                      <p class="text-xs font-medium uppercase tracking-wide text-base-content/80">Total</p>
                      <p class="mt-1 text-lg font-semibold">{{ disk_info.total_gb }} GB</p>
                  </article>
              </div>
          </div>
      </section>
      {% endif %}
  ```

- [ ] **Step 6: Run full view tests**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test main.tests.test_views -v 2
  ```
  Expected: all tests pass.

- [ ] **Step 7: Commit**

  ```bash
  git add django/main/views.py django/main/templates/pages/about.html django/main/tests/test_views.py
  git commit -m "feat: add disk usage panel to about page admin section"
  ```

---

## Task 10: Upgrade Node 20 → 22 in Dockerfile

**Files:**
- Modify: `infra/Dockerfile`

- [ ] **Step 1: Change the Node base image**

  Open `infra/Dockerfile`. Find line 2:
  ```dockerfile
  FROM node:20-slim AS css-builder
  ```
  Change to:
  ```dockerfile
  FROM node:22-slim AS css-builder
  ```

- [ ] **Step 2: Verify CSS build still works**

  ```bash
  npm run build:css:prod
  ```
  Expected: CSS file generated at `django/main/static/css/style.css` with no errors.

- [ ] **Step 3: Commit**

  ```bash
  git add infra/Dockerfile
  git commit -m "chore: upgrade Node 20 → 22 in Dockerfile (Node 20 EOL Apr 2026)"
  ```

---

## Task 11: Update Python package versions

**Files:**
- Modify: `uv.lock` (generated automatically)

- [ ] **Step 1: Upgrade patch-safe packages**

  ```bash
  uv lock --upgrade-package pillow --upgrade-package requests --upgrade-package bleach --upgrade-package django
  ```
  This updates `uv.lock` to the latest patch releases within the pinned major versions. Check what changed:
  ```bash
  git diff uv.lock | grep "^[-+].*version" | head -20
  ```

- [ ] **Step 2: Re-sync the virtual environment**

  ```bash
  uv sync --extra dev
  ```

- [ ] **Step 3: Run full verification**

  ```bash
  make verify
  ```
  Expected: all checks pass. If any test fails due to a package API change, investigate and fix before committing.

- [ ] **Step 4: Commit**

  ```bash
  git add uv.lock
  git commit -m "chore: update python packages to latest patch versions"
  ```

---

## Task 12: Upgrade PostgreSQL 13 → 16

**Files:**
- Modify: `infra/docker-compose.prod.yml`

> **Note:** Steps 1-3 are manual production operations performed on the DigitalOcean droplet, not code changes. Step 4 is the code change.

- [ ] **Step 1: Dump the current database (on the droplet)**

  SSH into the droplet, then:
  ```bash
  cd ~/my_django_portfolio

  # Get the running db container name
  docker ps --filter "name=db" --format "{{.Names}}"
  # Example output: my_django_portfolio-db-1

  # Dump the database
  docker exec my_django_portfolio-db-1 \
    pg_dump -U $DOCKER_DB_USER $DOCKER_DB_NAME \
    > ~/pg_backup_$(date +%F).sql

  # Verify the dump is non-empty
  wc -l ~/pg_backup_$(date +%F).sql
  ```
  Expected: thousands of lines. If the file is empty or errors out, stop and investigate before proceeding.

- [ ] **Step 2: Update `docker-compose.prod.yml` locally**

  Open `infra/docker-compose.prod.yml`. Find:
  ```yaml
  db:
    image: postgres:13
  ```
  Change to:
  ```yaml
  db:
    image: postgres:16
  ```

- [ ] **Step 3: Commit the compose change**

  ```bash
  git add infra/docker-compose.prod.yml
  git commit -m "chore: upgrade PostgreSQL 13 → 16 (13 EOL Nov 2025)"
  ```

- [ ] **Step 4: Deploy and perform the data migration (on the droplet)**

  After the commit is on `main` and the new image is pushed (CI/CD runs), SSH into the droplet:
  ```bash
  cd ~/my_django_portfolio

  # Stop all services
  docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml down

  # Remove the old postgres data volume (required — PG13 data is incompatible with PG16)
  docker volume rm my_django_portfolio_postgres_data

  # Pull and start the new stack (PG16 initializes fresh)
  docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml pull
  docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml up -d

  # Wait ~10 seconds for db to be healthy, then check
  sleep 10
  docker compose --env-file .env -p my_django_portfolio -f infra/docker-compose.prod.yml ps
  ```

- [ ] **Step 5: Restore the database dump (on the droplet)**

  ```bash
  # Get new db container name
  docker ps --filter "name=db" --format "{{.Names}}"

  # Restore — substitute the actual date in the filename
  docker exec -i my_django_portfolio-db-1 \
    psql -U $DOCKER_DB_USER $DOCKER_DB_NAME \
    < ~/pg_backup_2026-05-14.sql

  # Verify by checking table count
  docker exec my_django_portfolio-db-1 \
    psql -U $DOCKER_DB_USER $DOCKER_DB_NAME \
    -c "\dt" | wc -l
  ```
  Expected: 15+ tables listed.

- [ ] **Step 6: Verify the site works**

  Open the site in a browser. Check:
  - Home page loads
  - Projects page loads
  - Admin `/admin/` accessible

  ```bash
  make prod-status
  ```
  All services should show `Up`.

---

## Final verification

- [ ] **Run full suite locally**

  ```bash
  make verify
  ```
  Expected: all steps pass with no errors.

- [ ] **Run all tests individually to confirm no regressions**

  ```bash
  SECRET_KEY=test DJANGO_DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
    uv run python django/manage.py test -v 2
  ```
  Expected: all tests pass.

---

## Self-review notes

**Spec coverage check:**
- ✅ 1a Celery ignore_result → Task 2
- ✅ 1b Media file cleanup → Task 5
- ✅ 1c Disk monitoring task + about panel → Tasks 8, 9
- ✅ 2a img src filter → Task 6
- ✅ 2b .env.example warning → Task 7
- ✅ 3a debug_task removed → Task 1
- ✅ 3b whitenoise comment removed → Task 1
- ✅ 3c urllib → requests → Task 4
- ✅ 3d visitor_counter read-only → Task 3
- ✅ 4a postgres:13 → 16 → Task 12
- ✅ 4b Python packages → Task 11
- ✅ 4c Node 20 → 22 → Task 10

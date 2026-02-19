import datetime
import shutil
import tempfile

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from main.markdown_sync import sync_project_markdown
from main.models import PortfolioProfile, Project


class _DummyResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status
        self._cursor = 0
        self.headers = {}

    def read(self, size=-1):
        if size is None or size < 0:
            size = len(self._payload) - self._cursor
        if self._cursor >= len(self._payload):
            return b""
        start = self._cursor
        end = min(start + size, len(self._payload))
        self._cursor = end
        return self._payload[start:end]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


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

        def opener(request, timeout=20):
            return _DummyResponse(b"# New Content\n\nUpdated.")

        result = sync_project_markdown(project, opener=opener)

        self.assertTrue(result["updated"])
        project.refresh_from_db()
        project.markdown_file.open("rb")
        self.assertEqual(project.markdown_file.read().decode("utf-8"), "# New Content\n\nUpdated.")
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

        def opener(request, timeout=20):
            raise OSError("network down")

        result = sync_project_markdown(project, opener=opener)

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

        def opener(request, timeout=20):
            return _DummyResponse(oversized_payload)

        result = sync_project_markdown(project, opener=opener)

        self.assertFalse(result["updated"])
        self.assertEqual(result["reason"], "download_failed")
        self.assertIn("exceeds size limit", result["error"])

        project.refresh_from_db()
        self.assertEqual(project.markdown_file.name, old_name)
        project.markdown_file.open("rb")
        self.assertEqual(project.markdown_file.read().decode("utf-8"), "# Old")
        project.markdown_file.close()

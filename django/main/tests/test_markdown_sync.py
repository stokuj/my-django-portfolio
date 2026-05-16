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

import datetime
import shutil
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from django.core.files.base import ContentFile
from main.models import (
    HeatmapSnapshot,
    PageView,
    Project,
    Tag,
    TaskExecutionLog,
    TaskExecutionStatus,
)
from main.views import handler404, handler500


class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp(prefix="views-tests-media-")
        cls._override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            title="Test Project",
            short_description="A test project",
            date=datetime.date(2023, 1, 1),
            status="finished",
            blog_url="test-project-views",
        )
        self.tag = Tag.objects.create(name="python")
        self.project.tags.add(self.tag)
        PageView.objects.create(id=1, count=0)

    def test_home_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertIn("timeline_sections", response.context)

    def test_task_3_settings_remove_sites_framework_and_heatmap_api_base_url(self):
        self.assertNotIn("django.contrib.sites", settings.INSTALLED_APPS)
        self.assertFalse(hasattr(settings, "SITE_ID"))
        self.assertFalse(hasattr(settings, "HEATMAP_API_BASE_URL"))

    def test_heatmap_refresh_is_scheduled_hourly_via_celery_beat(self):
        schedule = settings.CELERY_BEAT_SCHEDULE["refresh-portfolio-heatmap-hourly"]

        self.assertEqual(
            schedule["task"],
            "main.tasks.refresh_portfolio_heatmap_cache_task",
        )
        self.assertEqual(schedule["kwargs"], {"schedule_next": False})

    def test_about_view(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/about.html")

    def test_about_shows_disabled_heatmap_for_anonymous_when_not_configured(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GitHub Contributions")
        self.assertContains(response, "GITHUB_HEATMAP_TOKEN")
        self.assertNotContains(response, "Scheduled Jobs")
        self.assertNotContains(response, "Heatmap Refresh (FastAPI)")

    def test_about_shows_heatmap_for_admin_when_not_configured(self):
        User = get_user_model()
        admin_user = User.objects.create_user(
            username="admin-no-token",
            email="admin-no-token@example.com",
            password="secret",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GitHub Contributions")
        self.assertContains(response, "Scheduled Jobs")
        self.assertContains(response, "Sync Heatmap")
        self.assertContains(response, "Sync Markdown")
        self.assertContains(response, "GITHUB_HEATMAP_TOKEN")
        self.assertNotContains(response, "Connect your GitHub account")
        self.assertNotContains(response, "/accounts/3rdparty/")
        self.assertNotContains(response, "/accounts/github/login/")
        self.assertNotContains(response, "Disconnect GitHub")
        self.assertNotContains(response, "Live from FastAPI")
        self.assertNotContains(response, "Heatmap Refresh (FastAPI)")
        self.assertContains(response, "Heatmap Refresh")

    def test_about_shows_executed_tasks_list_for_admin(self):
        User = get_user_model()
        admin_user = User.objects.create_user(
            username="admin-tasks",
            email="admin-tasks@example.com",
            password="secret",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(admin_user)

        older_time = timezone.now() - datetime.timedelta(hours=2)
        newer_time = timezone.now() - datetime.timedelta(minutes=20)

        TaskExecutionLog.objects.create(
            task_name="main.older_task",
            last_status=TaskExecutionStatus.STATUS_FAILURE,
            last_run_at=older_time,
            last_failed=1,
            last_total=1,
            last_error="older error",
        )
        TaskExecutionLog.objects.create(
            task_name="main.newer_task",
            last_status=TaskExecutionStatus.STATUS_SUCCESS,
            last_run_at=newer_time,
            last_updated=1,
            last_total=1,
        )

        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Executed Tasks")
        self.assertContains(response, "main.older_task")
        self.assertContains(response, "main.newer_task")

        content = response.content.decode()
        self.assertLess(
            content.find("main.newer_task"), content.find("main.older_task")
        )

    def test_about_shows_only_last_30_executed_tasks(self):
        User = get_user_model()
        admin_user = User.objects.create_user(
            username="admin-tasks-limit",
            email="admin-tasks-limit@example.com",
            password="secret",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(admin_user)

        now = timezone.now()
        for idx in range(35):
            TaskExecutionLog.objects.create(
                task_name=f"main.task_{idx}",
                last_status=TaskExecutionStatus.STATUS_SUCCESS,
                last_run_at=now - datetime.timedelta(minutes=idx),
                last_total=1,
                last_updated=1,
            )

        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "main.task_0")
        self.assertContains(response, "main.task_29")
        self.assertNotContains(response, "main.task_30")
        self.assertNotContains(response, "main.task_34")

    @patch("main.views.refresh_portfolio_heatmap_cache_task.delay")
    def test_run_heatmap_refresh_task_queues_job_for_staff(self, delay_mock):
        User = get_user_model()
        admin_user = User.objects.create_user(
            username="admin-run-heatmap",
            email="admin-run-heatmap@example.com",
            password="secret",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(admin_user)
        delay_mock.return_value.id = "task-123"

        response = self.client.post(
            reverse("run_heatmap_refresh_task"),
            data={"next": reverse("about")},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("about"))
        delay_mock.assert_called_once_with(schedule_next=False)

    @patch("main.views.get_configured_github_token", return_value="gho_visible_token")
    def test_about_shows_heatmap_for_anonymous_when_configured(self, _token_mock):
        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GitHub Contributions")
        self.assertNotContains(response, "Login with GitHub")
        self.assertNotContains(response, "Live from FastAPI")
        self.assertNotContains(response, "Heatmap Refresh (FastAPI)")

    @patch("main.views.get_configured_github_token", return_value="gho_valid_token")
    def test_about_heatmap_data_returns_public_admin_data(self, _token_mock):
        HeatmapSnapshot.objects.create(
            key="portfolio",
            username="portfolio-admin",
            total=12,
            weeks_count=2,
            fetched_at=timezone.now(),
            payload={
                "username": "portfolio-admin",
                "total": 12,
                "weeks": [{"days": []}, {"days": []}],
            },
        )

        response = self.client.get(reverse("about_heatmap_data"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["username"], "portfolio-admin")
        self.assertEqual(payload["total"], 12)
        self.assertEqual(payload["last_30_days_total"], 0)
        self.assertEqual(payload["weeks_count"], 2)

    @patch("main.views.get_configured_github_token", return_value="gho_valid_token")
    @patch("main.views.refresh_portfolio_heatmap_cache_task.apply_async")
    @patch("main.views.fetch_heatmap_data")
    def test_about_heatmap_data_fetches_sync_when_cache_missing(
        self, fetch_mock, apply_async_mock, _token_mock
    ):
        fetch_mock.return_value = (
            {
                "username": "portfolio-admin",
                "total": 21,
                "weeks": [
                    {
                        "days": [
                            {
                                "date": datetime.date.today().isoformat(),
                                "count": 3,
                            },
                            {
                                "date": (
                                    datetime.date.today() - datetime.timedelta(days=40)
                                ).isoformat(),
                                "count": 99,
                            },
                        ]
                    }
                ],
            },
            None,
        )

        response = self.client.get(reverse("about_heatmap_data"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["username"], "portfolio-admin")
        self.assertEqual(payload["total"], 21)
        self.assertEqual(payload["last_30_days_total"], 3)
        self.assertEqual(payload["weeks_count"], 1)
        fetch_mock.assert_called_once_with()
        apply_async_mock.assert_not_called()

    @patch("main.views.get_configured_github_token", return_value="gho_valid_token")
    @patch("main.views.fetch_heatmap_data", return_value=(None, "upstream failure"))
    def test_about_heatmap_data_serves_cached_snapshot_when_refresh_fails(
        self, fetch_mock, _token_mock
    ):
        HeatmapSnapshot.objects.create(
            key="portfolio",
            username="portfolio-admin",
            total=9,
            weeks_count=1,
            payload={
                "username": "portfolio-admin",
                "total": 9,
                "weeks": [{"days": []}],
            },
        )

        response = self.client.get(reverse("about_heatmap_data"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["username"], "portfolio-admin")
        self.assertEqual(payload["total"], 9)
        fetch_mock.assert_called_once_with()

    @patch("main.views.get_configured_github_token", return_value=None)
    def test_about_heatmap_data_shows_error_when_admin_github_token_missing(self, _token_mock):
        response = self.client.get(reverse("about_heatmap_data"))
        payload = response.json()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(payload["error"], "Heatmap is not configured.")

    def test_projects_view(self):
        response = self.client.get(reverse("projects"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects/index.html")
        self.assertIn("projects", response.context)
        self.assertIn("all_tags", response.context)
        self.assertContains(
            response, reverse("blog_detail", args=[self.project.blog_url])
        )

    def test_projects_view_uses_detail_link_when_blog_slug_missing(self):
        no_slug_project = Project.objects.create(
            title="No Slug Blog Project",
            short_description="Blog project without slug",
            date=datetime.date(2023, 2, 1),
            blog=True,
            blog_url=None,
            status="ongoing",
        )

        response = self.client.get(reverse("projects"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, no_slug_project.title)
        self.assertNotContains(response, "/blog/None")

    def test_projects_view_orders_projects_by_newest_date_first(self):
        newest_project = Project.objects.create(
            title="Newest Project",
            short_description="Most recent project",
            date=datetime.date(2024, 1, 1),
            status="finished",
            blog_url="newest-project",
        )

        response = self.client.get(reverse("projects"))

        self.assertEqual(response.status_code, 200)
        projects = list(response.context["projects"])
        self.assertEqual(projects[0], newest_project)

    def test_blog_detail_renders_existing_template(self):
        Project.objects.create(
            title="Template Exists Blog Project",
            short_description="A project with matching blog template",
            blog=True,
            blog_url="my-django-portfolio",
            status="finished",
        )
        response = self.client.get(reverse("blog_detail", args=["my-django-portfolio"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects/detail.html")

    def test_blog_detail_renders_even_without_markdown_file(self):
        Project.objects.create(
            title="Missing Blog Template",
            short_description="A project with no matching template",
            blog=True,
            blog_url="missing-template",
            status="finished",
        )

        response = self.client.get(reverse("blog_detail", args=["missing-template"]))
        self.assertEqual(response.status_code, 200)

    def test_blog_detail_loads_markdown_from_uploaded_file(self):
        markdown_file = SimpleUploadedFile(
            "readme.md",
            b"# Title\n\nSome text",
            content_type="text/markdown",
        )
        project = Project.objects.create(
            title="File Markdown Project",
            short_description="Project with uploaded markdown file",
            blog=True,
            blog_url="file-markdown-project",
            status="finished",
            markdown_file=markdown_file,
        )

        response = self.client.get(reverse("blog_detail", args=[project.blog_url]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Title</h1>", html=True)

    def test_blog_detail_sanitizes_script_tags_in_markdown(self):
        markdown_file = SimpleUploadedFile(
            "malicious-readme.md",
            b"# Title\n\n<script>alert('xss')</script>\n\nParagraph.",
            content_type="text/markdown",
        )
        project = Project.objects.create(
            title="Unsafe Markdown Project",
            short_description="Project with potentially unsafe markdown",
            blog=True,
            blog_url="unsafe-markdown-project",
            status="finished",
            markdown_file=markdown_file,
        )

        response = self.client.get(reverse("blog_detail", args=[project.blog_url]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Title</h1>", html=True)
        self.assertNotContains(response, "<script>")

    def test_blog_detail_sanitizes_unsafe_image_attributes(self):
        markdown_file = SimpleUploadedFile(
            "unsafe-image-readme.md",
            b"<img src='https://raw.githubusercontent.com/user/repo/img.png' alt='preview' onerror='alert(1)'>",
            content_type="text/markdown",
        )
        project = Project.objects.create(
            title="Unsafe Image Attributes Project",
            short_description="Project with unsafe image attributes",
            blog=True,
            blog_url="unsafe-image-attrs-project",
            status="finished",
            markdown_file=markdown_file,
        )

        response = self.client.get(reverse("blog_detail", args=[project.blog_url]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<img")
        self.assertContains(response, 'src="https://raw.githubusercontent.com/user/repo/img.png"')
        self.assertContains(response, 'alt="preview"')
        self.assertNotContains(response, "onerror")

    def test_blog_detail_keeps_safe_markdown_elements(self):
        markdown_file = SimpleUploadedFile(
            "safe-elements-readme.md",
            (
                b"# Table\n\n"
                b"| Name | Value |\n"
                b"| --- | --- |\n"
                b"| A | 1 |\n\n"
                b"[Example](https://example.com)\n"
            ),
            content_type="text/markdown",
        )
        project = Project.objects.create(
            title="Safe Markdown Elements Project",
            short_description="Project with valid markdown features",
            blog=True,
            blog_url="safe-markdown-elements-project",
            status="finished",
            markdown_file=markdown_file,
        )

        response = self.client.get(reverse("blog_detail", args=[project.blog_url]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<table>")
        self.assertContains(
            response, '<a href="https://example.com">Example</a>', html=True
        )

    def test_blog_detail_renders_inline_and_block_math_wrappers(self):
        markdown_file = SimpleUploadedFile(
            "math-readme.md",
            (b"Inline math $a^2 + b^2 = c^2$\n\n$$\\int_0^1 x^2\\,dx = \\frac{1}{3}$$"),
            content_type="text/markdown",
        )
        project = Project.objects.create(
            title="Math Markdown Project",
            short_description="Project with markdown math",
            blog=True,
            blog_url="math-markdown-project",
            status="finished",
            markdown_file=markdown_file,
        )

        response = self.client.get(reverse("blog_detail", args=[project.blog_url]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="arithmatex"')
        self.assertContains(response, "\\int_0^1 x^2")

    def test_blog_detail_includes_mathjax_assets(self):
        response = self.client.get(reverse("blog_detail", args=[self.project.blog_url]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mathjax-config.js")
        self.assertContains(
            response, "cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        )

    def test_blog_detail_includes_all_projects_for_sidebar(self):
        other_project = Project.objects.create(
            title="Sidebar Item Project",
            short_description="Project visible in sidebar list",
            blog=True,
            blog_url="sidebar-item-project",
            status="finished",
        )

        response = self.client.get(reverse("blog_detail", args=[self.project.blog_url]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("all_projects", response.context)
        self.assertIn(other_project, response.context["all_projects"])

    def test_blog_detail_builds_branch_agnostic_readme_url(self):
        project = Project.objects.create(
            title="README Link Project",
            short_description="Project with explicit GitHub URL",
            blog=True,
            blog_url="readme-link-project",
            github_url="https://github.com/example/readme-link-project",
            status="finished",
        )

        response = self.client.get(reverse("blog_detail", args=[project.blog_url]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["readme_url"],
            "https://github.com/example/readme-link-project#readme",
        )

    def test_run_markdown_sync_task_requires_staff_access(self):
        response = self.client.post(reverse("run_markdown_sync_task"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_run_markdown_sync_task_enqueues_task_for_staff(self):
        User = get_user_model()
        staff_user = User.objects.create_user(
            username="staff-user",
            email="staff@example.com",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        with patch("main.views.sync_project_markdowns_task.delay") as delay_mock:
            delay_mock.return_value.id = "task-123"
            response = self.client.post(
                reverse("run_markdown_sync_task"),
                {"next": reverse("home")},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
        delay_mock.assert_called_once_with(blog_slug=None)

    def test_run_markdown_sync_task_redirects_to_safe_next_path(self):
        User = get_user_model()
        staff_user = User.objects.create_user(
            username="staff-user-safe-next",
            email="staff-safe-next@example.com",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        with patch("main.views.sync_project_markdowns_task.delay") as delay_mock:
            delay_mock.return_value.id = "task-123"
            response = self.client.post(
                reverse("run_markdown_sync_task"),
                {"next": reverse("about")},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("about"))

    def test_run_markdown_sync_task_rejects_external_next_url(self):
        User = get_user_model()
        staff_user = User.objects.create_user(
            username="staff-user-external-next",
            email="staff-external-next@example.com",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        with patch("main.views.sync_project_markdowns_task.delay") as delay_mock:
            delay_mock.return_value.id = "task-123"
            response = self.client.post(
                reverse("run_markdown_sync_task"),
                {"next": "https://evil.example/phishing"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    def test_run_markdown_sync_task_rejects_external_http_referer(self):
        User = get_user_model()
        staff_user = User.objects.create_user(
            username="staff-user-external-referer",
            email="staff-external-referer@example.com",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        with patch("main.views.sync_project_markdowns_task.delay") as delay_mock:
            delay_mock.return_value.id = "task-123"
            response = self.client.post(
                reverse("run_markdown_sync_task"),
                HTTP_REFERER="https://evil.example/phishing",
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    def test_blog_detail_strips_external_img_src(self):
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


class ErrorHandlersTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_handler404_returns_custom_template(self):
        request = self.factory.get("/non-existent/")
        response = handler404(request, Exception("not found"))
        self.assertEqual(response.status_code, 404)
        self.assertIn("Page Not Found", response.content.decode())

    def test_handler500_returns_custom_template(self):
        request = self.factory.get("/error/")
        response = handler500(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn("Server Error", response.content.decode())

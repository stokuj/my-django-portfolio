import datetime
import shutil
import tempfile
from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

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
        SocialApp.objects.filter(provider="github").delete()
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

    def _create_github_token(self, user, token_value="gho_test_token"):
        site = Site.objects.get_current()
        social_app = SocialApp.objects.filter(provider="github").order_by("id").first()
        if not social_app:
            social_app = SocialApp.objects.create(
                provider="github",
                name="GitHub",
                client_id="test-client-id",
                secret="test-client-secret",
                key="",
            )
        social_app.sites.add(site)

        social_account = SocialAccount.objects.create(
            user=user,
            provider="github",
            uid=f"github-{user.pk}",
            extra_data={"login": user.username},
        )

        return SocialToken.objects.create(
            app=social_app,
            account=social_account,
            token=token_value,
        )

    def test_home_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertIn("timeline_sections", response.context)

    def test_about_view(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/about.html")

    def test_about_hides_heatmap_for_anonymous_when_not_configured(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "GitHub Contributions")
        self.assertNotContains(response, "Scheduled Jobs")

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
        self.assertNotContains(response, ">Logout<", html=False)
        self.assertContains(
            response, "Connect your GitHub account to enable the heatmap."
        )
        self.assertContains(response, "/accounts/3rdparty/")
        self.assertNotContains(response, "/accounts/github/login/")

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

    def test_about_disconnect_github_removes_admin_social_account(self):
        User = get_user_model()
        admin_user = User.objects.create_user(
            username="admin-disconnect",
            email="admin-disconnect@example.com",
            password="secret",
            is_superuser=True,
            is_staff=True,
        )
        token = self._create_github_token(
            admin_user, token_value="gho_disconnect_token"
        )
        self.client.force_login(admin_user)

        response = self.client.post(reverse("about_heatmap_disconnect"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("about"))
        self.assertFalse(SocialAccount.objects.filter(pk=token.account.pk).exists())
        self.assertFalse(SocialToken.objects.filter(pk=token.pk).exists())

    def test_about_disconnect_github_requires_login(self):
        response = self.client.post(reverse("about_heatmap_disconnect"))
        self.assertEqual(response.status_code, 302)

    def test_accounts_3rdparty_redirects_staff_to_github_connect(self):
        User = get_user_model()
        admin_user = User.objects.create_user(
            username="admin-connect",
            email="admin-connect@example.com",
            password="secret",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(admin_user)

        response = self.client.get("/accounts/3rdparty/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/github/login/?process=connect")

    def test_accounts_3rdparty_redirects_non_staff_to_home(self):
        User = get_user_model()
        regular_user = User.objects.create_user(
            username="regular-user",
            email="regular-user@example.com",
            password="secret",
            is_staff=False,
        )
        self.client.force_login(regular_user)

        response = self.client.get("/accounts/3rdparty/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

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
        delay_mock.assert_called_once_with(schedule_next=True)

    @patch("main.views.get_portfolio_github_token", return_value="gho_visible_token")
    def test_about_shows_heatmap_for_anonymous_when_configured(self, _token_mock):
        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GitHub Contributions")

    @patch("main.views.get_portfolio_github_token", return_value="gho_valid_token")
    def test_about_heatmap_data_returns_public_admin_data(self, _token_mock):
        HeatmapSnapshot.objects.create(
            key="portfolio",
            username="portfolio-admin",
            total=12,
            weeks_count=2,
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

    @patch("main.views.get_portfolio_github_token", return_value="gho_valid_token")
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
        fetch_mock.assert_called_once_with("gho_valid_token")
        apply_async_mock.assert_called_once_with(
            kwargs={"schedule_next": True},
            countdown=3600,
        )

    def test_about_heatmap_data_shows_error_when_admin_github_token_missing(self):
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
            b"<img src='x' alt='preview' onerror='alert(1)'>",
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
        self.assertContains(response, 'src="x"')
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

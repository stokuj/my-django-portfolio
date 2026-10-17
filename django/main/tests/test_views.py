import collections
import datetime
import shutil
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import (
    Client,
    RequestFactory,
    SimpleTestCase,
    TestCase,
    override_settings,
)
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from django.views import defaults

from main.models import (
    HeatmapSnapshot,
    PageView,
    PortfolioProfile,
    Project,
    Tag,
    TaskExecutionLog,
)
from main.views import _render_markdown_to_html


@override_settings(GITHUB_HEATMAP_TOKEN="")
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
        cache.clear()
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

    def test_nav_marks_current_page(self):
        response = self.client.get(reverse("about"))
        self.assertContains(response, 'aria-current="page"', count=2)
        self.assertContains(
            response,
            'class="btn btn-ghost text-xl ui-motion" aria-current="page">About me</a>',
        )

    def test_pages_have_meta_description(self):
        profile = PortfolioProfile.get_active()
        cases = [
            (reverse("home"), profile.home_intro),
            (reverse("about"), profile.about_intro),
            (reverse("blog_detail", args=[self.project.blog_url]), "A test project"),
        ]
        for url, description in cases:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(
                    response, f'<meta name="description" content="{description}">', html=True
                )

    def test_share_tags_use_absolute_urls(self):
        response = self.client.get(reverse("home"))
        self.assertContains(
            response,
            '<meta property="og:image" content="http://testserver/static/images/hero-bg.png">',
            html=True,
        )
        self.assertContains(
            response, '<meta property="og:url" content="http://testserver/">', html=True
        )
        self.assertContains(
            response, '<meta name="twitter:card" content="summary_large_image">', html=True
        )

    def test_blog_detail_share_tags_use_project_and_thumbnail(self):
        self.project.thumbnail = SimpleUploadedFile("thumb.png", b"png")
        self.project.save()
        response = self.client.get(reverse("blog_detail", args=[self.project.blog_url]))
        self.assertContains(
            response, '<meta property="og:title" content="Test Project">', html=True
        )
        self.assertContains(
            response, '<meta property="og:description" content="A test project">', html=True
        )
        self.assertContains(
            response,
            f'<meta property="og:image" content="http://testserver{self.project.thumbnail.url}">',
            html=True,
        )

    def test_blank_profile_links_are_not_rendered(self):
        PortfolioProfile.objects.update_or_create(
            is_active=True, defaults={"email": "", "github_url": "", "linkedin_url": ""}
        )
        response = self.client.get(reverse("about"))
        self.assertNotContains(response, 'href="#"')
        self.assertNotContains(response, 'aria-label="Open GitHub profile"')
        self.assertNotContains(response, "Contact Me")

    def test_settings_drop_sites_framework_and_heatmap_api_base_url(self):
        self.assertNotIn("django.contrib.sites", settings.INSTALLED_APPS)
        self.assertFalse(hasattr(settings, "SITE_ID"))
        self.assertFalse(hasattr(settings, "HEATMAP_API_BASE_URL"))

    def test_about_view(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/about.html")

    def test_about_shows_disabled_heatmap_for_anonymous_when_not_configured(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GitHub Contributions")
        self.assertFalse(response.context["heatmap_enabled"])
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
        self.assertFalse(response.context["heatmap_enabled"])
        self.assertContains(response, "Heatmap Refresh")

    def test_about_scheduled_jobs_show_latest_run_per_job(self):
        User = get_user_model()
        admin_user = User.objects.create_user(
            username="admin-jobs", password="secret", is_staff=True
        )
        self.client.force_login(admin_user)
        last_run = timezone.now() - datetime.timedelta(minutes=5)
        TaskExecutionLog.objects.create(
            task_name="main.refresh_portfolio_heatmap_cache_task",
            status=TaskExecutionLog.STATUS_FAILURE,
            run_at=last_run - datetime.timedelta(days=1),
        )
        TaskExecutionLog.objects.create(
            task_name="main.refresh_portfolio_heatmap_cache_task",
            status=TaskExecutionLog.STATUS_SUCCESS,
            run_at=last_run,
        )

        response = self.client.get(reverse("about"))

        jobs = {job["task_name"]: job for job in response.context["scheduled_jobs"]}
        self.assertEqual(
            set(jobs),
            {
                "main.refresh_portfolio_heatmap_cache_task",
                "main.sync_project_markdowns_task",
            },
        )
        heatmap = jobs["main.refresh_portfolio_heatmap_cache_task"]
        self.assertEqual(heatmap["label"], "Heatmap Refresh")
        self.assertEqual(heatmap["schedule_label"], "Hourly at :00")
        self.assertEqual(heatmap["status"], "success")
        self.assertEqual(heatmap["run_at"], last_run)
        self.assertEqual(jobs["main.sync_project_markdowns_task"]["status"], "never")

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
            status=TaskExecutionLog.STATUS_FAILURE,
            run_at=older_time,
            total=1,
            error="older error",
        )
        TaskExecutionLog.objects.create(
            task_name="main.newer_task",
            status=TaskExecutionLog.STATUS_SUCCESS,
            run_at=newer_time,
            updated=1,
            total=1,
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
                status=TaskExecutionLog.STATUS_SUCCESS,
                run_at=now - datetime.timedelta(minutes=idx),
                total=1,
                updated=1,
            )

        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "main.task_0")
        self.assertContains(response, "main.task_29")
        self.assertNotContains(response, "main.task_30")
        self.assertNotContains(response, "main.task_34")

    @patch(
        "main.views.refresh_portfolio_heatmap_cache_task",
        return_value={"ok": True, "total": 5},
    )
    def test_run_heatmap_refresh_task_runs_job_for_staff(self, task_mock):
        User = get_user_model()
        admin_user = User.objects.create_user(
            username="admin-run-heatmap",
            email="admin-run-heatmap@example.com",
            password="secret",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(admin_user)

        response = self.client.post(
            reverse("run_heatmap_refresh_task"),
            data={"next": reverse("about")},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("about"))
        task_mock.assert_called_once_with()
        self.assertIn(
            "Heatmap refreshed: 5 contributions.",
            [str(m) for m in get_messages(response.wsgi_request)],
        )

    @patch("main.views.get_configured_github_token", return_value="gho_visible_token")
    def test_about_shows_heatmap_for_anonymous_when_configured(self, _token_mock):
        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GitHub Contributions")
        self.assertTrue(response.context["heatmap_enabled"])

    @patch("main.views.get_configured_github_token", return_value="gho_valid_token")
    def test_about_heatmap_data_returns_public_admin_data(self, _token_mock):
        HeatmapSnapshot.objects.create(
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
        self.assertEqual(payload["weeks"], [{"days": []}, {"days": []}])
        self.assertEqual(
            set(payload),
            {"username", "total", "last_30_days_total", "fetched_at", "weeks"},
        )

    @patch("main.views.get_configured_github_token", return_value="gho_valid_token")
    @patch("main.heatmap.fetch_heatmap_data")
    def test_about_heatmap_data_without_payload_returns_503(self, fetch_mock, _token_mock):
        response = self.client.get(reverse("about_heatmap_data"))

        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.json())
        fetch_mock.assert_not_called()

    @patch("main.views.get_configured_github_token", return_value="gho_valid_token")
    @patch("main.heatmap.fetch_heatmap_data")
    def test_about_heatmap_data_serves_old_snapshot_without_fetching(
        self, fetch_mock, _token_mock
    ):
        HeatmapSnapshot.objects.create(
            fetched_at=timezone.now() - datetime.timedelta(days=1),
            payload={
                "username": "portfolio-admin",
                "total": 9,
                "weeks": [{"days": []}],
            },
        )

        for _ in range(5):
            response = self.client.get(reverse("about_heatmap_data"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["total"], 9)

        fetch_mock.assert_not_called()

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

    def test_projects_tag_filters_expose_pressed_state(self):
        response = self.client.get(reverse("projects"))
        self.assertContains(response, 'data-tag="all" type="button" aria-pressed="true"')
        self.assertContains(response, 'data-tag="python" type="button" aria-pressed="false"')

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

    def test_blog_detail_title_is_project_title(self):
        response = self.client.get(reverse("blog_detail", args=["test-project-views"]))
        self.assertContains(response, "<title>Test Project</title>", html=False)

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
        self.assertNotIn("<script", response.context["blog_markdown_html"])

    def test_blog_detail_sanitizes_unsafe_image_attributes(self):
        markdown_file = SimpleUploadedFile(
            "unsafe-image-readme.md",
            b"<img src='https://raw.githubusercontent.com/user/repo/img.png' alt='preview' "
            b"onerror='alert(1)'>",
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
            response, "cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"
        )
        self.assertContains(
            response,
            'integrity="sha384-Wuix6BuhrWbjDBs24bXrjf4ZQ5aFeFWBuKkFekO2t8xFU0iNaLQfp2K6/1Nxveei"',
        )
        self.assertContains(response, 'crossorigin="anonymous"')

    def test_blog_detail_sidebar_marks_current_project(self):
        response = self.client.get(reverse("blog_detail", args=[self.project.blog_url]))
        # The sidebar renders twice (mobile and desktop); the nav has no current link here.
        self.assertContains(response, 'aria-current="page"', count=2)
        self.assertContains(response, 'active" aria-current="page">')

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

    def test_blog_detail_sidebar_query_count_does_not_grow_with_projects(self):
        # A field the sidebar reads but .only() omits would cost one query per row.
        url = reverse("blog_detail", args=[self.project.blog_url])
        self.client.get(url)

        def count_queries():
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(url)
            return len(ctx.captured_queries)

        baseline = count_queries()
        for i in range(3):
            Project.objects.create(
                title=f"Sidebar Project {i}",
                short_description="Sidebar row",
                blog=i == 0,
                blog_url="sidebar-project-0" if i == 0 else None,
                github_url="https://github.com/example/repo" if i == 1 else "",
                status="finished",
            )
        self.assertEqual(count_queries(), baseline)

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
        self.assertContains(
            response, 'href="https://github.com/example/readme-link-project" target="_blank"'
        )

    def test_run_markdown_sync_task_requires_staff_access(self):
        response = self.client.post(reverse("run_markdown_sync_task"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_run_markdown_sync_task_runs_job_for_staff(self):
        User = get_user_model()
        staff_user = User.objects.create_user(
            username="staff-user",
            email="staff@example.com",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        with patch(
            "main.views.sync_project_markdowns_task",
            return_value={"total": 1, "updated": 1, "failed": 0},
        ) as task_mock:
            response = self.client.post(
                reverse("run_markdown_sync_task"),
                {"next": reverse("home")},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
        task_mock.assert_called_once_with()
        self.assertIn(
            "Markdown sync: 1/1 updated.",
            [str(m) for m in get_messages(response.wsgi_request)],
        )

    def test_run_markdown_sync_task_redirects_to_safe_next_path(self):
        User = get_user_model()
        staff_user = User.objects.create_user(
            username="staff-user-safe-next",
            email="staff-safe-next@example.com",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        with patch(
            "main.views.sync_project_markdowns_task",
            return_value={"total": 1, "updated": 1, "failed": 0},
        ):
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

        with patch(
            "main.views.sync_project_markdowns_task",
            return_value={"total": 1, "updated": 1, "failed": 0},
        ):
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

        with patch(
            "main.views.sync_project_markdowns_task",
            return_value={"total": 1, "updated": 1, "failed": 0},
        ):
            response = self.client.post(
                reverse("run_markdown_sync_task"),
                HTTP_REFERER="https://evil.example/phishing",
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    def test_admin_tool_views_report_job_failure(self):
        User = get_user_model()
        self.client.force_login(
            User.objects.create_user(username="staff-job-fail", password="x", is_staff=True)
        )
        cases = (
            ("run_markdown_sync_task", "main.views.sync_project_markdowns_task",
             {"total": 2, "updated": 1, "failed": 1}, "Markdown sync: 1/2 updated."),
            ("run_heatmap_refresh_task", "main.views.refresh_portfolio_heatmap_cache_task",
             {"ok": False, "error": "boom"}, "Heatmap refresh failed: boom"),
        )
        for url_name, task_path, result, error in cases:
            with self.subTest(url_name=url_name):
                with patch(task_path, return_value=result):
                    response = self.client.post(reverse(url_name), {"next": reverse("about")})

                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, reverse("about"))
                self.assertIn(error, [str(m) for m in get_messages(response.wsgi_request)])

    def test_blog_detail_strips_external_img_src(self):
        project = Project.objects.create(
            title="Img Test",
            short_description="img",
            date=datetime.date(2024, 1, 1),
            blog=True,
            blog_url="img-test-slug",
            status="finished",
        )
        kept_srcs = [
            "https://raw.githubusercontent.com/user/repo/main/img.png",
            "https://camo.githubusercontent.com/abc123/def456",
            "https://github.com/user/repo/assets/1/screenshot.png",
        ]
        external_md = "# Test\n\n![tracker](https://evil.com/pixel.gif)\n\n" + "".join(
            f"![github]({src})\n\n" for src in kept_srcs
        )
        project.markdown_file.save(
            "img-test-slug.md", ContentFile(external_md.encode()), save=True
        )

        response = self.client.get(reverse("blog_detail", args=["img-test-slug"]))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn("evil.com", content)
        for src in kept_srcs:
            self.assertIn(f'src="{src}"', content)

    def test_about_shows_disk_info_for_staff(self):
        User = get_user_model()
        staff = User.objects.create_user("diskstaff", password="pass", is_staff=True)
        self.client.force_login(staff)
        gb = 1024 ** 3
        DiskUsage = collections.namedtuple("DiskUsage", ["total", "used", "free"])

        # Level uses unrounded free space: 0.96 and 1.96 would round up past the thresholds.
        for free_gb, level in ((0.96, "critical"), (1.96, "warning")):
            with self.subTest(free_gb=free_gb):
                usage = DiskUsage(
                    total=10 * gb, used=int((10 - free_gb) * gb), free=int(free_gb * gb)
                )
                with patch("main.views.shutil.disk_usage", return_value=usage):
                    response = self.client.get(reverse("about"))

                self.assertEqual(response.status_code, 200)
                disk = response.context["disk_info"]
                self.assertEqual(disk["level"], level)
                self.assertEqual(disk["total_gb"], 10.0)


class ErrorHandlersTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_default_404_view_uses_custom_template(self):
        request = self.factory.get("/non-existent/")
        response = defaults.page_not_found(request, Exception("not found"))
        self.assertEqual(response.status_code, 404)
        self.assertIn("Page Not Found", response.content.decode())

    def test_default_500_view_uses_custom_template(self):
        request = self.factory.get("/error/")
        response = defaults.server_error(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn("Sorry, something went wrong on our end", response.content.decode())


class MarkdownSanitizerTest(SimpleTestCase):
    def test_class_attribute_allows_only_arithmatex(self):
        html = _render_markdown_to_html(
            '<div class="fixed inset-0 z-50">overlay</div>\n\n$x^2$'
        )

        self.assertNotIn("fixed inset-0", html)
        self.assertIn('class="arithmatex"', html)

    def test_dangerous_markdown_is_stripped(self):
        cases = [
            ("[x](javascript:alert(1))", ["javascript:"]),
            ("<a onclick=x style=y>link</a>", ["onclick", "style"]),
            ('<iframe src="https://example.com"></iframe>', ["<iframe"]),
            ('<img src="https://github.com.evil.tld/a.png">', ["evil.tld"]),
        ]
        for markdown_source, forbidden in cases:
            with self.subTest(markdown_source=markdown_source):
                html = _render_markdown_to_html(markdown_source)
                for token in forbidden:
                    self.assertNotIn(token, html)


class PageViewAdminTests(TestCase):
    def test_pageview_admin_blocks_add_and_delete(self):
        User = get_user_model()
        self.client.force_login(
            User.objects.create_superuser(username="root", password="secret")
        )
        PageView.get_instance()

        add = self.client.get(reverse("admin:main_pageview_add"))
        delete = self.client.get(reverse("admin:main_pageview_delete", args=[1]))
        change = self.client.get(reverse("admin:main_pageview_change", args=[1]))

        self.assertEqual(add.status_code, 403)
        self.assertEqual(delete.status_code, 403)
        self.assertEqual(change.status_code, 200)
        self.assertNotContains(change, 'name="count"')

    def test_project_and_task_log_changelists_render_filters(self):
        User = get_user_model()
        self.client.force_login(
            User.objects.create_superuser(username="root", password="secret")
        )
        Project.objects.create(title="Admin Project", short_description="x")
        TaskExecutionLog.objects.create(task_name="main.tasks.sync", status="success")

        projects = self.client.get(reverse("admin:main_project_changelist"))
        logs = self.client.get(reverse("admin:main_taskexecutionlog_changelist"))

        self.assertEqual(projects.status_code, 200)
        self.assertContains(projects, "By status")
        self.assertEqual(logs.status_code, 200)
        self.assertContains(logs, "By status")

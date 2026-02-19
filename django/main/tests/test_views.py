import datetime
import shutil
import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from main.models import PageView, Project, Tag
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
        self.assertTemplateUsed(response, "main/home.html")
        self.assertIn("timeline_sections", response.context)

    def test_about_view(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/about.html")

    def test_projects_view(self):
        response = self.client.get(reverse("projects"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/projects.html")
        self.assertIn("projects", response.context)
        self.assertIn("all_tags", response.context)
        self.assertContains(response, reverse("blog_detail", args=[self.project.blog_url]))

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
        self.assertTemplateUsed(response, "main/blog/detail.html")

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
        self.assertContains(response, '<a href="https://example.com">Example</a>', html=True)

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

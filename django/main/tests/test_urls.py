import datetime

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from main.models import PageView, Project


@override_settings(GITHUB_HEATMAP_TOKEN="")
class URLsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            title="Test Project",
            short_description="A test project",
            date=datetime.date(2023, 1, 1),
            status="finished",
            blog_url="test-project-urls",
        )
        PageView.objects.create(id=1, count=0)

    def test_home_url(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/home/")
        self.assertRedirects(response, "/", status_code=301)
        self.assertEqual(reverse("home"), "/")

    def test_about_url(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GitHub Contributions")
        self.assertFalse(response.context["heatmap_enabled"])

    def test_about_heatmap_data_returns_404_when_not_configured(self):
        response = self.client.get("/about/heatmap-data/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Heatmap is not configured."})

    def test_about_heatmap_disconnect_route_is_removed(self):
        response = self.client.post("/about/heatmap-disconnect/")
        self.assertEqual(response.status_code, 404)

    def test_sitemap_lists_pages_and_blog_projects(self):
        Project.objects.create(
            title="No Blog", short_description="x", blog=False, blog_url="no-blog"
        )

        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        for path in ("/", "/projects/", "/about/", "/blog/test-project-urls/"):
            self.assertContains(response, f"<loc>http://testserver{path}</loc>")
        self.assertNotContains(response, "no-blog")

    def test_projects_url(self):
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200)

    def test_run_markdown_sync_url_requires_staff(self):
        response = self.client.post("/admin-tools/run-markdown-sync/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_run_heatmap_refresh_url_requires_staff(self):
        response = self.client.post("/admin-tools/run-heatmap-refresh/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_accounts_login_route_is_removed(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 404)

    def test_accounts_3rdparty_route_is_removed(self):
        response = self.client.get("/accounts/3rdparty/")
        self.assertEqual(response.status_code, 404)

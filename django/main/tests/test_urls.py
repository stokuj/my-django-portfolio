import datetime

from django.test import Client, TestCase

from main.models import PageView, Project


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
        self.assertEqual(response.status_code, 200)

    def test_about_url(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)

    def test_projects_url(self):
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200)

    def test_project_detail_url(self):
        response = self.client.get(f"/projects/{self.project.id}/")
        self.assertEqual(response.status_code, 200)

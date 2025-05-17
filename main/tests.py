from django.test import TestCase, Client
from django.urls import reverse
from .models import Tag, Project, PageView
import datetime

class TagModelTest(TestCase):
    def test_tag_creation(self):
        tag = Tag.objects.create(name="python")
        self.assertEqual(tag.name, "PYTHON")
        self.assertEqual(str(tag), "PYTHON")

    def test_tag_uppercase_conversion(self):
        tag = Tag.objects.create(name="django")
        self.assertEqual(tag.name, "DJANGO")

class ProjectModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Test Project",
            short_description="A test project",
            date=datetime.date(2023, 1, 1),
            blog=True,
            blog_url="https://example.com/blog",
            github_url="https://github.com/example/test",
            status="finished"
        )
        self.tag1 = Tag.objects.create(name="python")
        self.tag2 = Tag.objects.create(name="django")
        self.project.tags.add(self.tag1, self.tag2)

    def test_project_creation(self):
        self.assertEqual(self.project.title, "Test Project")
        self.assertEqual(self.project.short_description, "A test project")
        self.assertEqual(self.project.date, datetime.date(2023, 1, 1))
        self.assertTrue(self.project.blog)
        self.assertEqual(self.project.blog_url, "https://example.com/blog")
        self.assertEqual(self.project.github_url, "https://github.com/example/test")
        self.assertEqual(self.project.status, "finished")
        self.assertEqual(str(self.project), "Test Project")

    def test_project_tags(self):
        self.assertEqual(self.project.tags.count(), 2)
        self.assertIn(self.tag1, self.project.tags.all())
        self.assertIn(self.tag2, self.project.tags.all())

class PageViewModelTest(TestCase):
    def test_pageview_creation(self):
        page_view = PageView.objects.create(count=10)
        self.assertEqual(page_view.count, 10)

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            title="Test Project",
            short_description="A test project",
            date=datetime.date(2023, 1, 1),
            status="finished"
        )
        self.tag = Tag.objects.create(name="python")
        self.project.tags.add(self.tag)
        PageView.objects.create(id=1, count=0)

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/home.html')
        self.assertIn('projects', response.context)

    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/about.html')

    def test_projects_view(self):
        response = self.client.get(reverse('projects'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/projects.html')
        self.assertIn('projects', response.context)
        self.assertIn('all_tags', response.context)

    def test_project_detail_view(self):
        response = self.client.get(reverse('project_detail', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/project_detail.html')
        self.assertIn('project', response.context)
        self.assertEqual(response.context['project'], self.project)

    def test_nonexistent_project_detail(self):
        response = self.client.get(reverse('project_detail', args=[999]))
        self.assertEqual(response.status_code, 404)

class URLsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            title="Test Project",
            short_description="A test project",
            date=datetime.date(2023, 1, 1),
            status="finished"
        )
        PageView.objects.create(id=1, count=0)

    def test_home_url(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)

    def test_about_url(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_projects_url(self):
        response = self.client.get('/projects/')
        self.assertEqual(response.status_code, 200)

    def test_project_detail_url(self):
        response = self.client.get(f'/projects/{self.project.id}/')
        self.assertEqual(response.status_code, 200)

    def test_blog_urls(self):
        # Test a few blog URLs
        response = self.client.get('/blog/test/')
        self.assertEqual(response.status_code, 200)

from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError
from django.core.exceptions import ValidationError
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
            blog_url="test-project-blog",
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
        self.assertEqual(self.project.blog_url, "test-project-blog")
        self.assertEqual(self.project.github_url, "https://github.com/example/test")
        self.assertEqual(self.project.status, "finished")
        self.assertEqual(str(self.project), "Test Project")

    def test_project_tags(self):
        self.assertEqual(self.project.tags.count(), 2)
        self.assertIn(self.tag1, self.project.tags.all())
        self.assertIn(self.tag2, self.project.tags.all())

    def test_multiple_projects_without_blog_url_can_be_created(self):
        first = Project.objects.create(
            title="No Blog URL 1",
            short_description="First project without blog URL",
            blog=False,
            status="planned",
        )
        second = Project.objects.create(
            title="No Blog URL 2",
            short_description="Second project without blog URL",
            blog=False,
            status="ongoing",
        )

        self.assertIsNone(first.blog_url)
        self.assertIsNone(second.blog_url)

    def test_non_empty_blog_url_must_remain_unique(self):
        Project.objects.create(
            title="Unique Blog URL 1",
            short_description="First project with URL",
            blog=True,
            blog_url="duplicate-slug",
            status="finished",
        )

        with self.assertRaises(IntegrityError):
            Project.objects.create(
                title="Unique Blog URL 2",
                short_description="Second project with same URL",
                blog=True,
                blog_url="duplicate-slug",
                status="finished",
            )

    def test_blog_url_must_be_slug_if_present(self):
        project = Project(
            title="Invalid Slug Project",
            short_description="Project with invalid blog URL format",
            blog=True,
            blog_url="https://example.com/blog",
            status="planned",
        )

        with self.assertRaises(ValidationError):
            project.full_clean()

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
            status="finished",
            blog_url="test-project-views"
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
        self.assertContains(response, '/blog/test-project-views')

    def test_projects_view_uses_detail_link_when_blog_slug_missing(self):
        no_slug_project = Project.objects.create(
            title="No Slug Blog Project",
            short_description="Blog project without slug",
            date=datetime.date(2023, 2, 1),
            blog=True,
            blog_url=None,
            status="ongoing",
        )

        response = self.client.get(reverse('projects'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'/projects/{no_slug_project.id}')
        self.assertNotContains(response, '/blog/None')

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
            status="finished",
            blog_url="test-project-urls"
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


class VisitorCountMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('home')
        self.about_url = reverse('about')

    def test_first_home_visit_increments_counter(self):
        self.client.get(self.home_url)
        self.assertEqual(PageView.get_instance().count, 1)

    def test_second_home_visit_in_same_session_does_not_increment(self):
        self.client.get(self.home_url)
        self.client.get(self.home_url)
        self.assertEqual(PageView.get_instance().count, 1)

    def test_home_visit_in_different_session_increments_again(self):
        self.client.get(self.home_url)
        second_client = Client()
        second_client.get(self.home_url)
        self.assertEqual(PageView.get_instance().count, 2)

    def test_home_alias_path_is_counted(self):
        self.client.get('/home/')
        self.assertEqual(PageView.get_instance().count, 1)

    def test_non_home_path_does_not_increment_counter(self):
        self.client.get(self.about_url)
        self.assertEqual(PageView.get_instance().count, 0)

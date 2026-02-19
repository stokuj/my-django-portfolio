import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from main.models import PageView, PortfolioProfile, Project, Tag


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
            tech_stack=["Python", "Django"],
            tools_libraries=["pytest", "requests"],
            status="finished",
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
        self.assertEqual(self.project.tech_stack, ["Python", "Django"])
        self.assertEqual(self.project.tools_libraries, ["pytest", "requests"])
        self.assertEqual(self.project.status, "finished")
        self.assertEqual(str(self.project), "Test Project")

    def test_project_json_fields_default_to_empty_lists(self):
        project = Project.objects.create(
            title="Defaults",
            short_description="Defaults test",
            blog=False,
            status="planned",
        )

        self.assertEqual(project.tech_stack, [])
        self.assertEqual(project.tools_libraries, [])
        self.assertEqual(project.markdown_content, "")

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


class PortfolioProfileModelTest(TestCase):
    def test_profile_defaults(self):
        profile = PortfolioProfile.objects.get(is_active=True)
        self.assertEqual(profile.site_name, "My Portfolio")
        self.assertEqual(profile.full_name, "John Doe")
        self.assertTrue(profile.is_active)

    def test_only_one_active_profile_is_allowed(self):
        with self.assertRaises(IntegrityError):
            PortfolioProfile.objects.create(full_name="Second Active", is_active=True)

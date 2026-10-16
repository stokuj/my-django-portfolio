from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Project


class StaticPagesSitemap(Sitemap):
    def items(self):
        return ["home", "projects", "about"]

    def location(self, item):
        return reverse(item)


class BlogSitemap(Sitemap):
    def items(self):
        return (
            Project.objects.filter(blog=True)
            .exclude(blog_url__isnull=True)
            .exclude(blog_url="")
            .order_by("-date", "-id")
        )

    def location(self, project):
        return reverse("blog_detail", args=[project.blog_url])

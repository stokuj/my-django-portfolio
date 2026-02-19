import datetime

from django.core.validators import FileExtensionValidator
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        self.name = self.name.upper()  # Zamiana na wielkie litery przed zapisem
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Project(models.Model):
    title = models.CharField(max_length=200)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    markdown_file = models.FileField(
        upload_to="blog_markdown/",
        validators=[FileExtensionValidator(allowed_extensions=["md"])],
        blank=True,
        null=True,
    )
    tech_stack = models.JSONField(default=list, blank=True)
    tools_libraries = models.JSONField(default=list, blank=True)
    short_description = models.CharField(max_length=100)
    date = models.DateField(default=datetime.date(2022, 5, 1))     
    blog = models.BooleanField(default=True)
    blog_url = models.SlugField(max_length=100, blank=True, null=True, default=None)
    github_url = models.CharField(max_length=100, blank=True, null=True)

    tags = models.ManyToManyField(Tag, blank=True)

    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('finished', 'Finished'),
    ]

    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='planned',)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["blog_url"],
                condition=models.Q(blog_url__isnull=False) & ~models.Q(blog_url=""),
                name="uniq_project_blog_url_when_present",
            ),
        ]

    def __str__(self):
        return self.title

class PageView(models.Model):
    count = models.IntegerField(default=0)

    @classmethod
    def get_instance(cls):
        """
        Singleton pattern implementation.
        Always returns the same instance of PageView.
        """
        instance, created = cls.objects.get_or_create(id=1)
        return instance


class PortfolioProfile(models.Model):
    site_name = models.CharField(max_length=100, default="My Portfolio")
    full_name = models.CharField(max_length=120, default="John Doe")
    role_line = models.CharField(
        max_length=160,
        default="Junior Full-Stack Developer & Data Science enthusiast",
    )
    specialization_line = models.CharField(
        max_length=160,
        default="Specialized in Python, Django, PostgreSQL",
    )
    email = models.EmailField(blank=True, default="example@mail.com")
    github_url = models.URLField(blank=True, default="https://github.com/your-username")
    linkedin_url = models.URLField(blank=True, default="https://www.linkedin.com/in/your-profile/")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=models.Q(is_active=True),
                name="uniq_active_portfolio_profile",
            ),
        ]

    def __str__(self):
        return self.full_name

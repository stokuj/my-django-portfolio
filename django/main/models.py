import datetime

from django.core.validators import FileExtensionValidator
from django.db import models

from .validators import validate_github_repo_url


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        self.name = self.name.upper()  # Zamiana na wielkie litery przed zapisem
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=200)
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
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
    github_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        validators=[validate_github_repo_url],
    )

    tags = models.ManyToManyField(Tag, blank=True)

    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("ongoing", "Ongoing"),
        ("finished", "Finished"),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="planned",
    )

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


class TaskExecutionStatus(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_PARTIAL_SUCCESS = "partial_success"
    STATUS_FAILURE = "failure"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Success"),
        (STATUS_PARTIAL_SUCCESS, "Partial success"),
        (STATUS_FAILURE, "Failure"),
    ]

    task_name = models.CharField(max_length=150, unique=True)
    last_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, blank=True, default=""
    )
    last_run_at = models.DateTimeField(blank=True, null=True)
    last_success_at = models.DateTimeField(blank=True, null=True)
    last_failure_at = models.DateTimeField(blank=True, null=True)
    last_total = models.PositiveIntegerField(default=0)
    last_updated = models.PositiveIntegerField(default=0)
    last_failed = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")

    def __str__(self):
        return self.task_name


class TaskExecutionLog(models.Model):
    task_name = models.CharField(max_length=150, db_index=True)
    last_status = models.CharField(
        max_length=20,
        choices=TaskExecutionStatus.STATUS_CHOICES,
        blank=True,
        default="",
    )
    last_run_at = models.DateTimeField(blank=True, null=True)
    last_success_at = models.DateTimeField(blank=True, null=True)
    last_failure_at = models.DateTimeField(blank=True, null=True)
    last_total = models.PositiveIntegerField(default=0)
    last_updated = models.PositiveIntegerField(default=0)
    last_failed = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task_name} @ {self.last_run_at}"


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
    home_intro = models.CharField(
        max_length=255,
        default="Junior Programmer and Data Science Enthusiast building practical web and analytics projects.",
    )
    about_intro = models.CharField(
        max_length=255,
        default=(
            "Junior Full-Stack and Data Science enthusiast focused on robust Django applications, "
            "clean architecture, and practical data tooling."
        ),
    )
    email = models.EmailField(blank=True, default="example@mail.com")
    github_url = models.URLField(blank=True, default="https://github.com/your-username")
    linkedin_url = models.URLField(
        blank=True, default="https://www.linkedin.com/in/your-profile/"
    )
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


class HeatmapSnapshot(models.Model):
    key = models.CharField(max_length=40, unique=True, default="portfolio")
    payload = models.JSONField(default=dict, blank=True)
    username = models.CharField(max_length=255, blank=True, default="")
    total = models.PositiveIntegerField(default=0)
    weeks_count = models.PositiveIntegerField(default=0)
    fetched_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, default="")

    def __str__(self):
        return f"HeatmapSnapshot<{self.key}>"

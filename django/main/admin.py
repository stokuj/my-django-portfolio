from django.contrib import admin
from .models import (
    PageView,
    PortfolioProfile,
    Project,
    Tag,
    TaskExecutionLog,
    TaskExecutionStatus,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "blog",
        "blog_url",
        "markdown_file",
        "tech_stack",
        "tools_libraries",
    )
    search_fields = ("title", "blog_url")


@admin.register(PortfolioProfile)
class PortfolioProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "site_name", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("full_name", "site_name", "email")
    fieldsets = (
        (
            "Profile",
            {
                "fields": (
                    "is_active",
                    "site_name",
                    "full_name",
                    "role_line",
                    "specialization_line",
                    "home_intro",
                    "about_intro",
                    "email",
                    "github_url",
                    "linkedin_url",
                )
            },
        ),
        (
            "About Page Lists",
            {
                "fields": (
                    "core_stack",
                    "current_learning",
                    "current_learning_summary",
                    "interests",
                )
            },
        ),
    )


@admin.register(TaskExecutionStatus)
class TaskExecutionStatusAdmin(admin.ModelAdmin):
    list_display = (
        "task_name",
        "last_status",
        "last_total",
        "last_updated",
        "last_failed",
        "last_run_at",
        "last_success_at",
        "last_failure_at",
    )
    readonly_fields = (
        "task_name",
        "last_status",
        "last_run_at",
        "last_success_at",
        "last_failure_at",
        "last_total",
        "last_updated",
        "last_failed",
        "last_error",
    )
    search_fields = ("task_name",)


@admin.register(TaskExecutionLog)
class TaskExecutionLogAdmin(admin.ModelAdmin):
    list_display = (
        "task_name",
        "last_status",
        "last_total",
        "last_updated",
        "last_failed",
        "last_run_at",
        "created_at",
    )
    readonly_fields = (
        "task_name",
        "last_status",
        "last_run_at",
        "last_success_at",
        "last_failure_at",
        "last_total",
        "last_updated",
        "last_failed",
        "last_error",
        "created_at",
    )
    search_fields = ("task_name", "last_error")


admin.site.register(Tag)
admin.site.register(PageView)

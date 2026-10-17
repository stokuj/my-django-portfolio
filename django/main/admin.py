from django.contrib import admin

from .models import (
    PageView,
    PortfolioProfile,
    Project,
    Tag,
    TaskExecutionLog,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "blog", "blog_url", "date")
    list_filter = ("status", "blog", "tags")
    filter_horizontal = ("tags",)
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


@admin.register(TaskExecutionLog)
class TaskExecutionLogAdmin(admin.ModelAdmin):
    list_display = (
        "task_name",
        "status",
        "total",
        "updated",
        "failed",
        "run_at",
        "created_at",
    )
    readonly_fields = (
        "task_name",
        "status",
        "run_at",
        "total",
        "updated",
        "failed",
        "error",
        "created_at",
    )
    list_filter = ("task_name", "status")
    date_hierarchy = "created_at"
    search_fields = ("task_name", "error")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    readonly_fields = ("count",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Tag)

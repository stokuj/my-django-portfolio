from django.contrib import admin
from .models import PageView, PortfolioProfile, Project, Tag


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "blog", "blog_url", "markdown_file", "tech_stack", "tools_libraries")
    search_fields = ("title", "blog_url")


@admin.register(PortfolioProfile)
class PortfolioProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "site_name", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("full_name", "site_name", "email")


admin.site.register(Tag)
admin.site.register(PageView)

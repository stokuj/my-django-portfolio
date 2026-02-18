from django.contrib import admin
from .models import Project, Tag, PageView


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "blog", "blog_url", "markdown_content", "tech_stack", "tools_libraries")
    search_fields = ("title", "blog_url")


admin.site.register(Tag)
admin.site.register(PageView)

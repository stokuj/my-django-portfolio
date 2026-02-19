from celery import shared_task

from .markdown_sync import sync_project_markdown
from .models import Project
@shared_task
def healthcheck_task():
    return "ok"


@shared_task
def sync_project_markdowns_task(blog_slug=None):
    projects = Project.objects.filter(blog=True)
    if blog_slug:
        projects = projects.filter(blog_url=blog_slug)

    results = []
    updated_count = 0
    for project in projects:
        result = sync_project_markdown(project)
        if result["updated"]:
            updated_count += 1
        results.append(result)

    return {
        "total": len(results),
        "updated": updated_count,
        "failed": len(results) - updated_count,
        "results": results,
    }

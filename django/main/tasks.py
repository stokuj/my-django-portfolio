import logging

from celery import shared_task
from django.utils import timezone

from .markdown_sync import sync_project_markdown
from .models import Project, TaskExecutionStatus

logger = logging.getLogger(__name__)
SYNC_MARKDOWNS_TASK_NAME = "main.sync_project_markdowns_task"


@shared_task
def healthcheck_task():
    return "ok"


@shared_task
def sync_project_markdowns_task(blog_slug=None):
    status, _ = TaskExecutionStatus.objects.get_or_create(task_name=SYNC_MARKDOWNS_TASK_NAME)
    status.last_run_at = timezone.now()

    projects = Project.objects.filter(blog=True)
    if blog_slug:
        projects = projects.filter(blog_url=blog_slug)

    results = []
    updated_count = 0
    for project in projects:
        try:
            result = sync_project_markdown(project)
        except Exception as exc:
            logger.exception(
                "Markdown sync task failed for project id=%s slug=%s",
                project.id,
                project.blog_url,
            )
            result = {
                "project_id": project.id,
                "slug": project.blog_url,
                "updated": False,
                "reason": "task_exception",
                "error": str(exc),
            }
        if result["updated"]:
            updated_count += 1
        results.append(result)

    failed_count = len(results) - updated_count
    status.last_total = len(results)
    status.last_updated = updated_count
    status.last_failed = failed_count

    if failed_count == 0:
        status.last_status = TaskExecutionStatus.STATUS_SUCCESS
        status.last_success_at = timezone.now()
        status.last_error = ""
    elif updated_count > 0:
        status.last_status = TaskExecutionStatus.STATUS_PARTIAL_SUCCESS
        status.last_failure_at = timezone.now()
        failed_results = [item for item in results if not item.get("updated")]
        status.last_error = "; ".join(
            f"{item.get('slug')}: {item.get('reason', 'unknown_error')}"
            for item in failed_results[:5]
        )
    else:
        failed_results = [item for item in results if not item.get("updated")]
        status.last_status = TaskExecutionStatus.STATUS_FAILURE
        status.last_failure_at = timezone.now()
        status.last_error = "; ".join(
            f"{item.get('slug')}: {item.get('reason', 'unknown_error')}"
            for item in failed_results[:5]
        )
    status.save(
        update_fields=[
            "last_status",
            "last_run_at",
            "last_success_at",
            "last_failure_at",
            "last_total",
            "last_updated",
            "last_failed",
            "last_error",
        ]
    )

    return {
        "total": len(results),
        "updated": updated_count,
        "failed": failed_count,
        "results": results,
    }

import logging
from datetime import timedelta

from django.utils import timezone

from .heatmap import (
    fetch_heatmap_data,
    update_snapshot_error,
    update_snapshot_with_payload,
)
from .markdown_sync import sync_project_markdown
from .models import Project, TaskExecutionLog

logger = logging.getLogger(__name__)
SYNC_MARKDOWNS_TASK_NAME = "main.sync_project_markdowns_task"
REFRESH_HEATMAP_TASK_NAME = "main.refresh_portfolio_heatmap_cache_task"
DISK_CRITICAL_GB = 1.0
DISK_WARNING_GB = 2.0
LOG_RETENTION_DAYS = 90


def disk_level(free_gb):
    """Classify free disk space as "critical", "warning" or "ok"."""
    if free_gb < DISK_CRITICAL_GB:
        return "critical"
    if free_gb < DISK_WARNING_GB:
        return "warning"
    return "ok"


def sync_project_markdowns_task():
    started_at = timezone.now()

    projects = Project.objects.filter(blog=True)

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
    failed_results = [item for item in results if not item.get("updated")]
    last_error = "; ".join(
        f"{item.get('slug')}: {item.get('reason', 'unknown_error')}"
        for item in failed_results[:5]
    )

    if failed_count == 0:
        state = TaskExecutionLog.STATUS_SUCCESS
    elif updated_count > 0:
        state = TaskExecutionLog.STATUS_PARTIAL_SUCCESS
    else:
        state = TaskExecutionLog.STATUS_FAILURE
    _finish(
        SYNC_MARKDOWNS_TASK_NAME,
        started_at,
        state,
        len(results),
        updated_count,
        last_error,
    )

    return {
        "total": len(results),
        "updated": updated_count,
        "failed": failed_count,
        "results": results,
    }


def refresh_portfolio_heatmap_cache_task():
    started_at = timezone.now()

    payload, error = fetch_heatmap_data()
    if error:
        update_snapshot_error(error)
        _finish(
            REFRESH_HEATMAP_TASK_NAME, started_at, TaskExecutionLog.STATUS_FAILURE, 1, 0, error
        )
        return {"ok": False, "error": error}

    snapshot = update_snapshot_with_payload(payload)
    _finish(REFRESH_HEATMAP_TASK_NAME, started_at, TaskExecutionLog.STATUS_SUCCESS, 1, 1)
    return {
        "ok": True,
        "username": snapshot.username,
        "total": snapshot.total,
        "weeks_count": snapshot.weeks_count,
    }


def _finish(task_name, started_at, state, total, updated, error=""):
    """Write the log row for a finished run (the only place log rows are written).

    Also prunes rows older than LOG_RETENTION_DAYS.
    """
    TaskExecutionLog.objects.create(
        task_name=task_name,
        last_status=state,
        last_run_at=started_at,
        last_total=total,
        last_updated=updated,
        last_failed=total - updated,
        last_error=error,
    )
    TaskExecutionLog.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=LOG_RETENTION_DAYS)
    ).delete()

import logging
import shutil

from celery import shared_task
from django.utils import timezone

from .heatmap import (
    fetch_heatmap_data,
    update_snapshot_error,
    update_snapshot_with_payload,
)
from .markdown_sync import sync_project_markdown
from .models import Project, TaskExecutionLog, TaskExecutionStatus

logger = logging.getLogger(__name__)
SYNC_MARKDOWNS_TASK_NAME = "main.sync_project_markdowns_task"
REFRESH_HEATMAP_TASK_NAME = "main.refresh_portfolio_heatmap_cache_task"
DISK_USAGE_TASK_NAME = "main.check_disk_usage_task"
DISK_CRITICAL_GB = 1.0
DISK_WARNING_GB = 2.0


@shared_task(ignore_result=True)
def healthcheck_task():
    return "ok"


@shared_task(ignore_result=True)
def sync_project_markdowns_task():
    status, _ = TaskExecutionStatus.objects.get_or_create(
        task_name=SYNC_MARKDOWNS_TASK_NAME
    )
    status.last_run_at = timezone.now()

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
        state = TaskExecutionStatus.STATUS_SUCCESS
    elif updated_count > 0:
        state = TaskExecutionStatus.STATUS_PARTIAL_SUCCESS
    else:
        state = TaskExecutionStatus.STATUS_FAILURE
    _finish(status, state, len(results), updated_count, last_error)

    return {
        "total": len(results),
        "updated": updated_count,
        "failed": failed_count,
        "results": results,
    }


@shared_task(ignore_result=True)
def refresh_portfolio_heatmap_cache_task():
    status, _ = TaskExecutionStatus.objects.get_or_create(
        task_name=REFRESH_HEATMAP_TASK_NAME
    )
    status.last_run_at = timezone.now()

    payload, error = fetch_heatmap_data()
    if error:
        update_snapshot_error(error)
        _finish(status, TaskExecutionStatus.STATUS_FAILURE, 1, 0, error)
        return {"ok": False, "error": error}

    snapshot = update_snapshot_with_payload(payload)
    _finish(status, TaskExecutionStatus.STATUS_SUCCESS, 1, 1)
    return {
        "ok": True,
        "username": snapshot.username,
        "total": snapshot.total,
        "weeks_count": snapshot.weeks_count,
    }


@shared_task(ignore_result=True)
def check_disk_usage_task():
    usage = shutil.disk_usage("/")
    free_gb = usage.free / (1024 ** 3)

    status, _ = TaskExecutionStatus.objects.get_or_create(task_name=DISK_USAGE_TASK_NAME)
    status.last_run_at = timezone.now()

    if free_gb < DISK_CRITICAL_GB:
        logger.critical("DISK CRITICAL: only %.1f GB free on /", free_gb)
        _finish(
            status,
            TaskExecutionStatus.STATUS_FAILURE,
            1,
            0,
            f"CRITICAL: {free_gb:.1f} GB free (below {DISK_CRITICAL_GB} GB threshold)",
        )
    elif free_gb < DISK_WARNING_GB:
        logger.warning("DISK WARNING: only %.1f GB free on /", free_gb)
        _finish(
            status,
            TaskExecutionStatus.STATUS_PARTIAL_SUCCESS,
            1,
            0,
            f"WARNING: {free_gb:.1f} GB free (below {DISK_WARNING_GB} GB threshold)",
        )
    else:
        logger.info("DISK OK: %.1f GB free on /", free_gb)
        _finish(status, TaskExecutionStatus.STATUS_SUCCESS, 1, 1)


def _finish(status, state, total, updated, error=""):
    """Record a finished run on the status row and append a log entry."""
    status.last_status = state
    if state == TaskExecutionStatus.STATUS_SUCCESS:
        status.last_success_at = timezone.now()
    else:
        status.last_failure_at = timezone.now()
    status.last_total = total
    status.last_updated = updated
    status.last_failed = total - updated
    status.last_error = error
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
    _log_task_execution(status)


def _log_task_execution(status):
    TaskExecutionLog.objects.create(
        task_name=status.task_name,
        last_status=status.last_status,
        last_run_at=status.last_run_at,
        last_success_at=status.last_success_at,
        last_failure_at=status.last_failure_at,
        last_total=status.last_total,
        last_updated=status.last_updated,
        last_failed=status.last_failed,
        last_error=status.last_error,
    )

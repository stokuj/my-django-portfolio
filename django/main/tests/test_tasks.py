import collections
from unittest.mock import patch

from django.test import TestCase, override_settings

from main.models import HeatmapSnapshot, Project, TaskExecutionLog
from main.tasks import (
    DISK_USAGE_TASK_NAME,
    REFRESH_HEATMAP_TASK_NAME,
    SYNC_MARKDOWNS_TASK_NAME,
    check_disk_usage_task,
    healthcheck_task,
    refresh_portfolio_heatmap_cache_task,
    sync_project_markdowns_task,
)


class TaskStatusTrackingTests(TestCase):
    def test_sync_task_updates_status_on_success(self):
        project = Project.objects.create(
            title="Task Success",
            short_description="sync task",
            blog=True,
            blog_url="task-success",
            status="finished",
        )

        with patch(
            "main.tasks.sync_project_markdown",
            return_value={
                "project_id": project.id,
                "slug": project.blog_url,
                "updated": True,
            },
        ):
            result = sync_project_markdowns_task()

        log = TaskExecutionLog.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_SUCCESS)
        self.assertEqual(log.last_total, 1)
        self.assertEqual(log.last_updated, 1)
        self.assertEqual(log.last_failed, 0)
        self.assertIsNotNone(log.last_run_at)
        self.assertEqual(log.last_error, "")

    def test_sync_task_updates_status_on_failure(self):
        Project.objects.create(
            title="Task Failure",
            short_description="sync task",
            blog=True,
            blog_url="task-failure",
            status="finished",
        )

        with patch(
            "main.tasks.sync_project_markdown",
            return_value={
                "project_id": 1,
                "slug": "task-failure",
                "updated": False,
                "reason": "download_failed",
                "error": "network down",
            },
        ):
            result = sync_project_markdowns_task()

        log = TaskExecutionLog.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_FAILURE)
        self.assertEqual(log.last_total, 1)
        self.assertEqual(log.last_updated, 0)
        self.assertEqual(log.last_failed, 1)
        self.assertIsNotNone(log.last_run_at)
        self.assertIn("task-failure: download_failed", log.last_error)

    def test_sync_task_updates_status_on_partial_success(self):
        first = Project.objects.create(
            title="Task Partial 1",
            short_description="sync task",
            blog=True,
            blog_url="task-partial-1",
            status="finished",
        )
        Project.objects.create(
            title="Task Partial 2",
            short_description="sync task",
            blog=True,
            blog_url="task-partial-2",
            status="finished",
        )

        def _sync_side_effect(project):
            if project.id == first.id:
                return {
                    "project_id": project.id,
                    "slug": project.blog_url,
                    "updated": True,
                }
            return {
                "project_id": project.id,
                "slug": project.blog_url,
                "updated": False,
                "reason": "download_failed",
            }

        with patch("main.tasks.sync_project_markdown", side_effect=_sync_side_effect):
            result = sync_project_markdowns_task()

        log = TaskExecutionLog.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_PARTIAL_SUCCESS)
        self.assertEqual(log.last_total, 2)
        self.assertEqual(log.last_updated, 1)
        self.assertEqual(log.last_failed, 1)

    def test_sync_task_records_task_exception_as_partial_success(self):
        first = Project.objects.create(
            title="Task Raise 1",
            short_description="sync task",
            blog=True,
            blog_url="task-raise-1",
            status="finished",
        )
        Project.objects.create(
            title="Task Raise 2",
            short_description="sync task",
            blog=True,
            blog_url="task-raise-2",
            status="finished",
        )

        def _sync_side_effect(project):
            if project.id == first.id:
                return {"project_id": project.id, "slug": project.blog_url, "updated": True}
            raise RuntimeError("boom")

        with patch("main.tasks.sync_project_markdown", side_effect=_sync_side_effect):
            result = sync_project_markdowns_task()

        log = TaskExecutionLog.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_PARTIAL_SUCCESS)
        self.assertEqual(log.last_total, 2)
        self.assertEqual(log.last_updated, 1)
        self.assertEqual(log.last_failed, 1)
        self.assertIn("task-raise-2: task_exception", log.last_error)

    @patch("main.tasks.fetch_heatmap_data", return_value=(None, "boom"))
    def test_heatmap_refresh_task_records_fetch_error(self, fetch_mock):
        result = refresh_portfolio_heatmap_cache_task()

        log = TaskExecutionLog.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)
        snapshot = HeatmapSnapshot.objects.get(key="portfolio")
        self.assertEqual(result, {"ok": False, "error": "boom"})
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_FAILURE)
        self.assertEqual(log.last_failed, 1)
        self.assertEqual(log.last_error, "boom")
        self.assertEqual(snapshot.last_error, "boom")

    @patch("main.tasks.fetch_heatmap_data")
    def test_heatmap_refresh_task_updates_status_on_success(self, fetch_mock):
        fetch_mock.return_value = (
            {
                "username": "portfolio-admin",
                "total": 17,
                "weeks": [{"days": []}],
            },
            None,
        )

        result = refresh_portfolio_heatmap_cache_task()

        log = TaskExecutionLog.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)
        snapshot = HeatmapSnapshot.objects.get(key="portfolio")
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["username"], "portfolio-admin")
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_SUCCESS)
        self.assertEqual(log.last_total, 1)
        self.assertEqual(log.last_updated, 1)
        self.assertEqual(log.last_failed, 0)
        self.assertEqual(log.last_error, "")
        self.assertEqual(snapshot.username, "portfolio-admin")
        fetch_mock.assert_called_once_with()

    @patch("main.tasks.update_snapshot_error")
    @override_settings(GITHUB_HEATMAP_TOKEN="")
    def test_heatmap_refresh_task_updates_status_on_missing_token_failure(
        self, update_error_mock
    ):
        result = refresh_portfolio_heatmap_cache_task()

        log = TaskExecutionLog.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)
        self.assertEqual(
            result,
            {"ok": False, "error": "Heatmap is not configured."},
        )
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_FAILURE)
        self.assertEqual(log.last_total, 1)
        self.assertEqual(log.last_updated, 0)
        self.assertEqual(log.last_failed, 1)
        self.assertEqual(log.last_error, "Heatmap is not configured.")
        update_error_mock.assert_called_once_with("Heatmap is not configured.")


class TaskIgnoreResultTests(TestCase):
    def test_healthcheck_task_has_ignore_result(self):
        self.assertTrue(getattr(healthcheck_task, "ignore_result", False))


class DiskUsageTaskTests(TestCase):
    def _fake_usage(self, total_gb, free_gb):
        total = int(total_gb * 1024 ** 3)
        free = int(free_gb * 1024 ** 3)
        used = total - free
        DiskUsage = collections.namedtuple("DiskUsage", ["total", "used", "free"])
        return DiskUsage(total=total, used=used, free=free)

    def test_disk_task_success_when_ample_space(self):
        usage = self._fake_usage(total_gb=10.0, free_gb=5.0)
        with patch("main.tasks.shutil.disk_usage", return_value=usage):
            check_disk_usage_task()

        log = TaskExecutionLog.objects.get(task_name=DISK_USAGE_TASK_NAME)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_SUCCESS)
        self.assertEqual(log.last_error, "")

    def test_disk_task_partial_when_below_2gb(self):
        usage = self._fake_usage(total_gb=10.0, free_gb=1.5)
        with patch("main.tasks.shutil.disk_usage", return_value=usage):
            check_disk_usage_task()

        log = TaskExecutionLog.objects.get(task_name=DISK_USAGE_TASK_NAME)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_PARTIAL_SUCCESS)
        self.assertIn("1.5", log.last_error)

    def test_disk_task_failure_when_below_1gb(self):
        usage = self._fake_usage(total_gb=10.0, free_gb=0.8)
        with patch("main.tasks.shutil.disk_usage", return_value=usage):
            check_disk_usage_task()

        log = TaskExecutionLog.objects.get(task_name=DISK_USAGE_TASK_NAME)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_FAILURE)
        self.assertIn("CRITICAL", log.last_error)

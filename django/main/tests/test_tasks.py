from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from main.models import HeatmapSnapshot, Project, TaskExecutionLog
from main.tasks import (
    REFRESH_HEATMAP_TASK_NAME,
    SYNC_MARKDOWNS_TASK_NAME,
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


class TaskLogRetentionTests(TestCase):
    def test_finished_run_deletes_log_rows_older_than_90_days(self):
        old = TaskExecutionLog.objects.create(task_name=REFRESH_HEATMAP_TASK_NAME)
        recent = TaskExecutionLog.objects.create(task_name=REFRESH_HEATMAP_TASK_NAME)
        now = timezone.now()
        TaskExecutionLog.objects.filter(pk=old.pk).update(created_at=now - timedelta(days=91))
        TaskExecutionLog.objects.filter(pk=recent.pk).update(created_at=now - timedelta(days=89))

        with patch("main.tasks.fetch_heatmap_data", return_value=(None, "boom")):
            refresh_portfolio_heatmap_cache_task()

        self.assertFalse(TaskExecutionLog.objects.filter(pk=old.pk).exists())
        self.assertTrue(TaskExecutionLog.objects.filter(pk=recent.pk).exists())
        self.assertEqual(TaskExecutionLog.objects.count(), 2)


class JobCommandTests(TestCase):
    @patch("main.tasks.fetch_heatmap_data")
    def test_refresh_heatmap_command_logs_success(self, fetch_mock):
        fetch_mock.return_value = ({"username": "u", "total": 3, "weeks": []}, None)
        out = StringIO()

        call_command("refresh_heatmap", stdout=out)

        log = TaskExecutionLog.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_SUCCESS)
        self.assertIn("3 contributions", out.getvalue())

    @patch("main.tasks.fetch_heatmap_data", return_value=(None, "boom"))
    def test_refresh_heatmap_command_fails_on_error(self, _fetch_mock):
        with self.assertRaisesMessage(CommandError, "boom"):
            call_command("refresh_heatmap")

        log = TaskExecutionLog.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_FAILURE)

    @patch("main.tasks.sync_project_markdown", return_value={"updated": True})
    def test_sync_markdowns_command_logs_success(self, _sync_mock):
        Project.objects.create(title="Cmd", blog=True, blog_url="cmd")
        out = StringIO()

        call_command("sync_markdowns", stdout=out)

        log = TaskExecutionLog.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_SUCCESS)
        self.assertIn("1/1 updated", out.getvalue())

    @patch(
        "main.tasks.sync_project_markdown",
        return_value={"slug": "cmd", "updated": False, "reason": "http_404"},
    )
    def test_sync_markdowns_command_fails_when_a_project_fails(self, _sync_mock):
        Project.objects.create(title="Cmd", blog=True, blog_url="cmd")

        with self.assertRaisesMessage(CommandError, "0/1 updated"):
            call_command("sync_markdowns")

        log = TaskExecutionLog.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertEqual(log.last_status, TaskExecutionLog.STATUS_FAILURE)

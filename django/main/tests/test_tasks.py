from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from main.models import HeatmapSnapshot, Project, TaskExecutionLog, TaskExecutionStatus
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

        status = TaskExecutionStatus.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        execution_log = TaskExecutionLog.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_SUCCESS)
        self.assertEqual(status.last_total, 1)
        self.assertEqual(status.last_updated, 1)
        self.assertEqual(status.last_failed, 0)
        self.assertIsNotNone(status.last_run_at)
        self.assertIsNotNone(status.last_success_at)
        self.assertIsNone(status.last_failure_at)
        self.assertEqual(status.last_error, "")
        self.assertEqual(execution_log.last_status, TaskExecutionStatus.STATUS_SUCCESS)
        self.assertEqual(execution_log.last_total, 1)
        self.assertEqual(execution_log.last_updated, 1)
        self.assertEqual(execution_log.last_failed, 0)

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

        status = TaskExecutionStatus.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        execution_log = TaskExecutionLog.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_FAILURE)
        self.assertEqual(status.last_total, 1)
        self.assertEqual(status.last_updated, 0)
        self.assertEqual(status.last_failed, 1)
        self.assertIsNotNone(status.last_run_at)
        self.assertIsNotNone(status.last_failure_at)
        self.assertIn("task-failure: download_failed", status.last_error)
        self.assertEqual(execution_log.last_status, TaskExecutionStatus.STATUS_FAILURE)
        self.assertEqual(execution_log.last_failed, 1)

    def test_sync_task_updates_status_on_partial_success(self):
        first = Project.objects.create(
            title="Task Partial 1",
            short_description="sync task",
            blog=True,
            blog_url="task-partial-1",
            status="finished",
        )
        second = Project.objects.create(
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

        status = TaskExecutionStatus.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        execution_log = TaskExecutionLog.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_PARTIAL_SUCCESS)
        self.assertEqual(status.last_total, 2)
        self.assertEqual(status.last_updated, 1)
        self.assertEqual(status.last_failed, 1)
        self.assertEqual(
            execution_log.last_status, TaskExecutionStatus.STATUS_PARTIAL_SUCCESS
        )
        self.assertEqual(execution_log.last_total, 2)

    def test_sync_task_clears_failure_timestamp_after_success(self):
        project = Project.objects.create(
            title="Task Success Transition",
            short_description="sync task",
            blog=True,
            blog_url="task-success-transition",
            status="finished",
        )
        TaskExecutionStatus.objects.create(
            task_name=SYNC_MARKDOWNS_TASK_NAME,
            last_status=TaskExecutionStatus.STATUS_FAILURE,
            last_failure_at=timezone.now(),
        )

        with patch(
            "main.tasks.sync_project_markdown",
            return_value={
                "project_id": project.id,
                "slug": project.blog_url,
                "updated": True,
            },
        ):
            sync_project_markdowns_task()

        status = TaskExecutionStatus.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertIsNotNone(status.last_success_at)
        self.assertIsNone(status.last_failure_at)

    def test_sync_task_clears_success_timestamp_after_failure(self):
        Project.objects.create(
            title="Task Failure Transition",
            short_description="sync task",
            blog=True,
            blog_url="task-failure-transition",
            status="finished",
        )
        TaskExecutionStatus.objects.create(
            task_name=SYNC_MARKDOWNS_TASK_NAME,
            last_status=TaskExecutionStatus.STATUS_SUCCESS,
            last_success_at=timezone.now(),
        )

        with patch(
            "main.tasks.sync_project_markdown",
            return_value={
                "project_id": 1,
                "slug": "task-failure-transition",
                "updated": False,
                "reason": "download_failed",
            },
        ):
            sync_project_markdowns_task()

        status = TaskExecutionStatus.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertIsNone(status.last_success_at)
        self.assertIsNotNone(status.last_failure_at)

    def test_sync_task_clears_success_timestamp_after_partial_success(self):
        first = Project.objects.create(
            title="Task Partial Transition 1",
            short_description="sync task",
            blog=True,
            blog_url="task-partial-transition-1",
            status="finished",
        )
        second = Project.objects.create(
            title="Task Partial Transition 2",
            short_description="sync task",
            blog=True,
            blog_url="task-partial-transition-2",
            status="finished",
        )
        TaskExecutionStatus.objects.create(
            task_name=SYNC_MARKDOWNS_TASK_NAME,
            last_status=TaskExecutionStatus.STATUS_SUCCESS,
            last_success_at=timezone.now(),
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
            sync_project_markdowns_task()

        status = TaskExecutionStatus.objects.get(task_name=SYNC_MARKDOWNS_TASK_NAME)
        self.assertIsNone(status.last_success_at)
        self.assertIsNotNone(status.last_failure_at)

    @patch("main.tasks.fetch_heatmap_data")
    @patch("main.tasks.get_configured_github_token", return_value="gho_task_token")
    def test_heatmap_refresh_task_updates_status_on_success(
        self, _token_mock, fetch_mock
    ):
        fetch_mock.return_value = (
            {
                "username": "portfolio-admin",
                "total": 17,
                "weeks": [{"days": []}],
            },
            None,
        )

        result = refresh_portfolio_heatmap_cache_task()

        status = TaskExecutionStatus.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)
        execution_log = TaskExecutionLog.objects.get(
            task_name=REFRESH_HEATMAP_TASK_NAME
        )
        snapshot = HeatmapSnapshot.objects.get(key="portfolio")
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["username"], "portfolio-admin")
        self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_SUCCESS)
        self.assertEqual(status.last_total, 1)
        self.assertEqual(status.last_updated, 1)
        self.assertEqual(status.last_failed, 0)
        self.assertEqual(status.last_error, "")
        self.assertEqual(execution_log.last_status, TaskExecutionStatus.STATUS_SUCCESS)
        self.assertEqual(snapshot.username, "portfolio-admin")
        fetch_mock.assert_called_once_with()

    @patch("main.tasks.fetch_heatmap_data")
    @patch("main.tasks.get_configured_github_token", return_value="gho_task_token")
    def test_heatmap_refresh_task_clears_failure_timestamp_after_success(
        self, _token_mock, fetch_mock
    ):
        TaskExecutionStatus.objects.create(
            task_name=REFRESH_HEATMAP_TASK_NAME,
            last_status=TaskExecutionStatus.STATUS_FAILURE,
            last_failure_at=timezone.now(),
        )
        status = TaskExecutionStatus.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)

        fetch_mock.return_value = (
            {
                "username": "portfolio-admin",
                "total": 17,
                "weeks": [{"days": []}],
            },
            None,
        )

        refresh_portfolio_heatmap_cache_task()

        status.refresh_from_db()
        self.assertIsNone(status.last_failure_at)
        self.assertIsNotNone(status.last_success_at)

    @patch("main.tasks.update_snapshot_error")
    @patch("main.tasks.get_configured_github_token", return_value=None)
    def test_heatmap_refresh_task_updates_status_on_missing_token_failure(
        self, _token_mock, update_error_mock
    ):
        result = refresh_portfolio_heatmap_cache_task()

        status = TaskExecutionStatus.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)
        execution_log = TaskExecutionLog.objects.get(
            task_name=REFRESH_HEATMAP_TASK_NAME
        )
        self.assertEqual(
            result,
            {"ok": False, "error": "Heatmap is not configured."},
        )
        self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_FAILURE)
        self.assertEqual(status.last_total, 1)
        self.assertEqual(status.last_updated, 0)
        self.assertEqual(status.last_failed, 1)
        self.assertEqual(status.last_error, "Heatmap is not configured.")
        self.assertEqual(execution_log.last_status, TaskExecutionStatus.STATUS_FAILURE)
        update_error_mock.assert_called_once_with("Heatmap is not configured.")

    @patch("main.tasks.update_snapshot_error")
    @patch("main.tasks.get_configured_github_token", return_value=None)
    def test_heatmap_refresh_task_clears_success_timestamp_after_failure(
        self, _token_mock, update_error_mock
    ):
        TaskExecutionStatus.objects.create(
            task_name=REFRESH_HEATMAP_TASK_NAME,
            last_status=TaskExecutionStatus.STATUS_SUCCESS,
            last_success_at=timezone.now(),
        )
        status = TaskExecutionStatus.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)

        refresh_portfolio_heatmap_cache_task()

        status.refresh_from_db()
        self.assertIsNone(status.last_success_at)
        self.assertIsNotNone(status.last_failure_at)
        update_error_mock.assert_called_once_with("Heatmap is not configured.")

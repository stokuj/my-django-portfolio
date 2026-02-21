from unittest.mock import patch

from django.test import TestCase

from main.models import Project, TaskExecutionLog, TaskExecutionStatus
from main.tasks import SYNC_MARKDOWNS_TASK_NAME, sync_project_markdowns_task


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

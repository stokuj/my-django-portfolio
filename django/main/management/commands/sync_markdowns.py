from django.core.management.base import BaseCommand, CommandError

from main.tasks import sync_project_markdowns_task


class Command(BaseCommand):
    help = "Download README markdown for every blog project (run every 2 h by cron)."

    def handle(self, *args, **options):
        result = sync_project_markdowns_task()
        summary = f"Markdown sync: {result['updated']}/{result['total']} updated."
        if result["failed"]:
            raise CommandError(summary)
        self.stdout.write(summary)

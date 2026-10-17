from django.core.management.base import BaseCommand, CommandError

from main.tasks import refresh_portfolio_heatmap_cache_task


class Command(BaseCommand):
    help = "Fetch GitHub contributions into the heatmap snapshot (run hourly by cron)."

    def handle(self, *args, **options):
        result = refresh_portfolio_heatmap_cache_task()
        if not result["ok"]:
            raise CommandError(f"Heatmap refresh failed: {result['error']}")
        self.stdout.write(f"Heatmap refreshed: {result['total']} contributions.")

from django.core.management.base import BaseCommand, CommandError

from main.markdown_sync import sync_project_markdown
from main.models import Project


class Command(BaseCommand):
    help = "Fetch README markdown files and update Project.markdown_file when download succeeds."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            dest="slug",
            help="Sync only one project by blog slug.",
        )

    def handle(self, *args, **options):
        slug = options.get("slug")
        queryset = Project.objects.filter(blog=True)
        if slug:
            queryset = queryset.filter(blog_url=slug)

        projects = list(queryset)
        if slug and not projects:
            raise CommandError(f"Project with slug '{slug}' was not found.")

        updated = 0
        failed = 0

        for project in projects:
            result = sync_project_markdown(project)
            if result["updated"]:
                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[UPDATED] {project.blog_url} <- {result.get('source_url')}"
                    )
                )
            else:
                failed += 1
                reason = result.get("reason", "unknown")
                error = result.get("error", "")
                details = f"{reason}: {error}" if error else reason
                self.stdout.write(
                    self.style.WARNING(
                        f"[SKIPPED] {project.blog_url or project.id} ({details})"
                    )
                )

        self.stdout.write(
            f"Done. Total: {len(projects)}, updated: {updated}, failed: {failed}."
        )

from pathlib import Path

from django.db import migrations, models


def copy_markdown_into_db(apps, schema_editor):
    Project = apps.get_model("main", "Project")
    content_dir = Path(__file__).resolve().parents[1] / "content" / "blog"

    for project in Project.objects.all():
        markdown_content = ""
        markdown_file = getattr(project, "markdown_file", None)

        if markdown_file:
            try:
                markdown_file.open("rb")
                markdown_content = markdown_file.read().decode("utf-8")
            except (OSError, UnicodeDecodeError):
                markdown_content = ""
            finally:
                try:
                    markdown_file.close()
                except OSError:
                    pass

        if not markdown_content and project.blog_url:
            fallback_path = content_dir / f"{project.blog_url}.md"
            try:
                markdown_content = fallback_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                markdown_content = ""

        if markdown_content:
            project.markdown_content = markdown_content
            project.save(update_fields=["markdown_content"])


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0008_project_tech_stack_project_tools_libraries"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="markdown_content",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(copy_markdown_into_db, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="project",
            name="markdown_file",
        ),
    ]

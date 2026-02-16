from django.db import migrations, models


def normalize_empty_blog_url_to_null(apps, schema_editor):
    Project = apps.get_model("main", "Project")
    Project.objects.filter(blog_url="").update(blog_url=None)


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0003_alter_project_blog_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="blog_url",
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.RunPython(
            normalize_empty_blog_url_to_null, migrations.RunPython.noop
        ),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.UniqueConstraint(
                condition=models.Q(blog_url__isnull=False) & ~models.Q(blog_url=""),
                fields=("blog_url",),
                name="uniq_project_blog_url_when_present",
            ),
        ),
    ]

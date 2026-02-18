from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_alter_project_thumbnail"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="markdown_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="blog_markdown/",
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=["md"])],
            ),
        ),
    ]

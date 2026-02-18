from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_alter_project_blog_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="thumbnail",
            field=models.ImageField(blank=True, null=True, upload_to="thumbnails/"),
        ),
    ]

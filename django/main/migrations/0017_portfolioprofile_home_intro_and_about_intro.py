from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0016_alter_project_github_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="portfolioprofile",
            name="about_intro",
            field=models.CharField(
                default="Junior Full-Stack and Data Science enthusiast focused on robust Django applications, clean architecture, and practical data tooling.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="portfolioprofile",
            name="home_intro",
            field=models.CharField(
                default="Junior Programmer and Data Science Enthusiast building practical web and analytics projects.",
                max_length=255,
            ),
        ),
    ]

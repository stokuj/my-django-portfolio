from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0024_heatmapsnapshot_drop_derived_fields"),
    ]

    operations = [
        migrations.RenameField("taskexecutionlog", "last_status", "status"),
        migrations.RenameField("taskexecutionlog", "last_run_at", "run_at"),
        migrations.RenameField("taskexecutionlog", "last_total", "total"),
        migrations.RenameField("taskexecutionlog", "last_updated", "updated"),
        migrations.RenameField("taskexecutionlog", "last_error", "error"),
        migrations.RemoveField("taskexecutionlog", "last_failed"),
    ]

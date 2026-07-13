from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("service", "0002_machine_unique_serial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="repairjob",
            options={
                "ordering": ["-created_at"],
                "permissions": [("view_management_dashboard", "Can view management dashboard")],
            },
        ),
    ]

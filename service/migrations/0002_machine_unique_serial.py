from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("service", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="machine",
            constraint=models.UniqueConstraint(
                condition=~models.Q(("serial_number", "")),
                fields=("serial_number",),
                name="unique_machine_serial_when_present",
            ),
        ),
        migrations.AlterModelOptions(
            name="machine",
            options={"ordering": ["client__name", "machine_type", "brand", "model_name"]},
        ),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("service", "0003_repairjob_management_dashboard_permission")]
    operations = [migrations.CreateModel(name="ActivityLog", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("area", models.CharField(choices=[("repair", "Repair"), ("warranty", "Warranty")], max_length=20)),
        ("job_number", models.CharField(max_length=20)), ("action", models.CharField(max_length=100)),
        ("details", models.CharField(blank=True, max_length=255)), ("created_at", models.DateTimeField(auto_now_add=True)),
        ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ["-created_at"]})]

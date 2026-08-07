from django.db import migrations


def create_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Repair Desk")
    Group.objects.get_or_create(name="Warranty Desk")


def remove_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Repair Desk").delete()
    Group.objects.filter(name="Warranty Desk").delete()


class Migration(migrations.Migration):
    dependencies = [("service", "0009_repairjob_repaired_by")]
    operations = [migrations.RunPython(create_roles, remove_roles)]

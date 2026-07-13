from django.db import migrations


def create_ceo_group_and_remove_legacy_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group.objects.get_or_create(name="CEO")
    content_type = ContentType.objects.filter(app_label="service", model="repairjob").first()
    if content_type:
        Permission.objects.filter(
            content_type=content_type,
            codename="view_management_dashboard",
        ).delete()


class Migration(migrations.Migration):
    dependencies = [("service", "0004_activitylog")]

    operations = [
        migrations.AlterModelOptions(
            name="repairjob",
            options={"ordering": ["-created_at"]},
        ),
        migrations.RunPython(create_ceo_group_and_remove_legacy_permission, migrations.RunPython.noop),
    ]

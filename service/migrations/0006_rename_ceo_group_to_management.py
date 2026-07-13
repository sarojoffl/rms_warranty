from django.db import migrations


def rename_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    legacy_group = Group.objects.filter(name="CEO").first()
    management_group, _ = Group.objects.get_or_create(name="Management")
    if legacy_group and legacy_group.pk != management_group.pk:
        management_group.user_set.add(*legacy_group.user_set.all())
        legacy_group.delete()


class Migration(migrations.Migration):
    dependencies = [("service", "0005_ceo_group_role")]
    operations = [migrations.RunPython(rename_group, migrations.RunPython.noop)]

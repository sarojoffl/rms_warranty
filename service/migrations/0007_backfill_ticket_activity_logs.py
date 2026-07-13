from django.db import migrations


def backfill_ticket_logs(apps, schema_editor):
    ActivityLog = apps.get_model("service", "ActivityLog")
    RepairJob = apps.get_model("service", "RepairJob")
    WarrantyClaim = apps.get_model("service", "WarrantyClaim")

    for job in RepairJob.objects.all():
        ActivityLog.objects.get_or_create(
            area="repair",
            job_number=job.job_number,
            action="Repair intake logged",
            defaults={"details": job.problem_cause[:255]},
        )
        if job.status == "completed":
            ActivityLog.objects.get_or_create(
                area="repair",
                job_number=job.job_number,
                action="Repair exit updated",
                defaults={"details": job.solution_detail[:255]},
            )

    for claim in WarrantyClaim.objects.all():
        ActivityLog.objects.get_or_create(
            area="warranty",
            job_number=claim.job_number,
            action="Warranty claim logged",
            defaults={"details": claim.report_warranty_claimed[:255]},
        )
        if claim.solved:
            ActivityLog.objects.get_or_create(
                area="warranty",
                job_number=claim.job_number,
                action="Warranty exit updated",
                defaults={"details": claim.not_solved_cause[:255]},
            )


class Migration(migrations.Migration):
    dependencies = [("service", "0006_rename_ceo_group_to_management")]
    operations = [migrations.RunPython(backfill_ticket_logs, migrations.RunPython.noop)]

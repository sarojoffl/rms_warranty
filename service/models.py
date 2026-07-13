from django.db import models
from django.db.models import Max


# ---------------------------------------------------------------------------
# Shared: Client & Machine
# ---------------------------------------------------------------------------

class Client(models.Model):
    """A person/company who brings in a machine — used by both RMS and Warranty."""
    name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True, help_text="Optional")
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.company_name})" if self.company_name else self.name


class Machine(models.Model):
    """A specific device belonging to a client. Reused across RMS and Warranty entries."""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="machines")
    machine_type = models.CharField(max_length=100, help_text="e.g. Laptop, Printer, CCTV")
    brand = models.CharField(max_length=100, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True, help_text="Any other identifying details")

    class Meta:
        ordering = ["client__name", "machine_type", "brand", "model_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["serial_number"],
                condition=~models.Q(serial_number=""),
                name="unique_machine_serial_when_present",
            )
        ]

    def __str__(self):
        parts = [self.brand, self.model_name]
        label = " ".join(p for p in parts if p) or self.machine_type
        return f"{label} (S/N: {self.serial_number or '—'})"


# ---------------------------------------------------------------------------
# Helper for sequential job numbers
# ---------------------------------------------------------------------------

def _next_job_number(model, prefix):
    last = model.objects.aggregate(n=Max("id"))["n"] or 0
    return f"{prefix}-{last + 1:06d}"


# ---------------------------------------------------------------------------
# RMS workflow
# ---------------------------------------------------------------------------

class RepairJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"

    job_number = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # --- Entry form ---
    date_in = models.DateField()
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="repair_jobs")
    received_by = models.CharField(max_length=150, help_text="Who brought the machine in")
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name="repair_jobs")
    problem_cause = models.TextField(help_text="Problem / cause reported at intake")

    # --- Exit form (filled later; other details auto-fill from above) ---
    date_out = models.DateField(null=True, blank=True)
    solution_detail = models.TextField(blank=True)
    taken_by = models.CharField(max_length=150, blank=True, help_text="Who collected the machine")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.job_number:
            self.job_number = _next_job_number(RepairJob, "RMS")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job_number} — {self.client}"

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED


# ---------------------------------------------------------------------------
# Warranty workflow
# ---------------------------------------------------------------------------

class WarrantyClaim(models.Model):
    class Claimable(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"

    class RepairStatus(models.TextChoices):
        SOLVED = "solved", "Solved"
        NOT_SOLVED = "not_solved", "Not Solved"

    job_number = models.CharField(max_length=20, unique=True, editable=False, blank=True)

    # --- Entry form ---
    date_in = models.DateField()
    received_by = models.CharField(max_length=150)
    sold_to = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="warranty_claims",
                                 help_text="Client details")
    bought_from = models.CharField(max_length=200, blank=True)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name="warranty_claims")
    warranty_sent_date = models.DateField(null=True, blank=True, help_text="Editable")
    claimable = models.CharField(max_length=10, choices=Claimable.choices, blank=True)
    report_warranty_claimed = models.TextField(blank=True, help_text="Filled if claimable = Yes")

    # --- Exit form (auto-fills entry details in the UI) ---
    solved = models.CharField(max_length=15, choices=RepairStatus.choices, blank=True)
    not_solved_cause = models.TextField(blank=True, help_text="Required if not solved")
    sent_date_out = models.DateField(null=True, blank=True)
    report_complete = models.BooleanField(default=False, help_text="Complete or not")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.job_number:
            self.job_number = _next_job_number(WarrantyClaim, "WAR")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job_number} — {self.sold_to}"


class ActivityLog(models.Model):
    class Area(models.TextChoices):
        REPAIR = "repair", "Repair"
        WARRANTY = "warranty", "Warranty"

    actor = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    area = models.CharField(max_length=20, choices=Area.choices)
    job_number = models.CharField(max_length=20)
    action = models.CharField(max_length=100)
    details = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.job_number}: {self.action}"

from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    ClientForm, MachineForm, RepairJobEntryForm, RepairJobExitForm,
    WarrantyClaimEntryForm, WarrantyClaimExitForm,
)
from .models import ActivityLog, Client, Machine, RepairJob, WarrantyClaim
from .pdf_utils import build_report_pdf

MANAGEMENT_GROUP = "Management"


def is_management_user(user):
    """Management group members receive the reporting-only area."""
    return user.is_authenticated and user.groups.filter(name=MANAGEMENT_GROUP).exists()


def helpdesk_required(view_func):
    """Keep reporting-only management accounts out of ticket screens."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if is_management_user(request.user):
            return redirect("management_dashboard")
        return view_func(request, *args, **kwargs)
    return wrapped_view


def log_activity(request, area, job_number, action, details=""):
    ActivityLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        area=area, job_number=job_number, action=action, details=details,
    )


def management_required(view_func):
    """Allow the management page only to users in the Management group."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not is_management_user(request.user):
            return HttpResponseForbidden("You do not have access to management reporting.")
        return view_func(request, *args, **kwargs)
    return wrapped_view


class RoleAwareLoginView(auth_views.LoginView):
    """Send users to the dashboard that matches their granted access."""

    def get_success_url(self):
        if is_management_user(self.request.user):
            return reverse("management_dashboard")
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        return reverse("dashboard")


# ---------------------------------------------------------------------------
# Quick-create: Client / Machine (used from the intake forms via "+ New" links)
# ---------------------------------------------------------------------------

@login_required
def machine_options(request):
    """Return the assets owned by a selected client for intake-form selects."""
    client_id = request.GET.get("client_id")
    machines = Machine.objects.none()
    if client_id and client_id.isdigit():
        machines = Machine.objects.filter(client_id=client_id)
    return JsonResponse({
        "machines": [
            {"id": machine.pk, "label": str(machine)}
            for machine in machines
        ]
    })

def _safe_next(request, fallback):
    """Only redirect to a same-site path, never an open redirect."""
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and nxt.startswith("/"):
        return nxt
    return fallback


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"Client '{client.name}' added.")
            return redirect(_safe_next(request, "repair_create"))
    else:
        form = ClientForm()
    return render(request, "service/quick_form.html", {
        "form": form, "title": "New Client",
        "next": request.GET.get("next", ""),
    })


@login_required
def machine_create(request):
    if request.method == "POST":
        form = MachineForm(request.POST)
        if form.is_valid():
            machine = form.save()
            messages.success(request, f"Machine added for {machine.client.name}.")
            return redirect(_safe_next(request, "repair_create"))
    else:
        form = MachineForm()
    return render(request, "service/quick_form.html", {
        "form": form, "title": "New Machine",
        "next": request.GET.get("next", ""),
    })


# ---------------------------------------------------------------------------
# RMS (Repair) workflow
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    """Operational overview for staff at the start of a service-desk shift."""
    repairs = RepairJob.objects.select_related("client", "machine")
    claims = WarrantyClaim.objects.select_related("sold_to", "machine")
    return render(request, "service/dashboard.html", {
        "client_count": Client.objects.count(),
        "machine_count": Machine.objects.count(),
        "repair_total": repairs.count(),
        "repair_pending": repairs.filter(status=RepairJob.Status.PENDING).count(),
        "claim_total": claims.count(),
        "claim_open": claims.filter(solved="").count(),
        "claim_review": claims.filter(claimable="").count(),
        "recent_repairs": repairs[:5],
        "recent_claims": claims[:5],
    })


@management_required
def management_dashboard(request):
    """Read-only KPI overview for management users."""
    today = date.today()
    month_start = today.replace(day=1)
    period_start = today - timedelta(days=30)
    repairs = RepairJob.objects.all()
    claims = WarrantyClaim.objects.all()
    completed_this_month = repairs.filter(
        status=RepairJob.Status.COMPLETED,
        date_out__gte=month_start,
    )
    turnaround_days = [
        (job.date_out - job.date_in).days
        for job in completed_this_month.only("date_in", "date_out")
        if job.date_out
    ]

    return render(request, "service/management_dashboard.html", {
        "month_start": month_start,
        "today": today,
        "repairs_received_month": repairs.filter(date_in__gte=month_start).count(),
        "repairs_completed_month": completed_this_month.count(),
        "repair_backlog": repairs.filter(status=RepairJob.Status.PENDING).count(),
        "average_turnaround": round(sum(turnaround_days) / len(turnaround_days), 1) if turnaround_days else None,
        "claims_received_month": claims.filter(date_in__gte=month_start).count(),
        "claims_claimable_month": claims.filter(
            date_in__gte=month_start,
            claimable=WarrantyClaim.Claimable.YES,
        ).count(),
        "claims_open": claims.filter(solved="").count(),
        "repairs_last_30_days": repairs.filter(date_in__gte=period_start).count(),
        "claims_last_30_days": claims.filter(date_in__gte=period_start).count(),
        "recent_logs": ActivityLog.objects.select_related("actor")[:6],
    })


@management_required
def management_logs(request):
    return render(request, "service/management_logs.html", {
        "logs": ActivityLog.objects.select_related("actor"),
    })

@login_required
def repair_list(request):
    jobs = RepairJob.objects.select_related("client", "machine")
    status = request.GET.get("status")
    if status in ("pending", "completed"):
        jobs = jobs.filter(status=status)
    return render(request, "service/repair_list.html", {"jobs": jobs, "status": status})


@login_required
def repair_create(request):
    """Entry form."""
    if request.method == "POST":
        form = RepairJobEntryForm(request.POST)
        if form.is_valid():
            job = form.save()
            log_activity(request, ActivityLog.Area.REPAIR, job.job_number, "Repair intake logged", job.problem_cause[:255])
            messages.success(request, f"Repair job {job.job_number} logged.")
            return redirect("repair_detail", pk=job.pk)
    else:
        form = RepairJobEntryForm(initial={"date_in": date.today()})
    return render(request, "service/repair_form.html", {"form": form, "mode": "entry"})


@login_required
def repair_exit(request, pk):
    """Exit form — other details auto-fill from the entry via the template context."""
    job = get_object_or_404(RepairJob, pk=pk)
    if request.method == "POST":
        form = RepairJobExitForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            log_activity(request, ActivityLog.Area.REPAIR, job.job_number, "Repair exit updated", job.solution_detail[:255])
            messages.success(request, f"Repair job {job.job_number} updated.")
            return redirect("repair_detail", pk=job.pk)
    else:
        initial = {"date_out": date.today()} if not job.date_out else {}
        form = RepairJobExitForm(instance=job, initial=initial)
    return render(request, "service/repair_form.html", {"form": form, "mode": "exit", "job": job})


@login_required
def repair_detail(request, pk):
    job = get_object_or_404(RepairJob.objects.select_related("client", "machine"), pk=pk)
    return render(request, "service/repair_detail.html", {"job": job})


@login_required
def repair_export_pdf(request, pk):
    job = get_object_or_404(RepairJob.objects.select_related("client", "machine"), pk=pk)
    rows = [
        ("Job Number", job.job_number),
        ("Status", job.get_status_display()),
        ("Date In", job.date_in),
        ("Client", job.client.name),
        ("Company", job.client.company_name),
        ("Received By", job.received_by),
        ("Machine", f"{job.machine.machine_type} — {job.machine.brand} {job.machine.model_name}"),
        ("Serial Number", job.machine.serial_number),
        ("Problem / Cause", job.problem_cause),
        ("Date Out", job.date_out),
        ("Solution / Repair Detail", job.solution_detail),
        ("Taken By", job.taken_by),
    ]
    return build_report_pdf(
        filename=f"repair_{job.job_number}.pdf",
        title="RMS — Repair Job Report",
        subtitle=f"Generated on {date.today()}",
        field_rows=rows,
    )


# ---------------------------------------------------------------------------
# Warranty workflow
# ---------------------------------------------------------------------------

@login_required
def warranty_list(request):
    claims = WarrantyClaim.objects.select_related("sold_to", "machine")
    claimable = request.GET.get("claimable")
    if claimable in ("yes", "no"):
        claims = claims.filter(claimable=claimable)
    return render(request, "service/warranty_list.html", {"claims": claims, "claimable": claimable})


@login_required
def warranty_create(request):
    """Entry form."""
    if request.method == "POST":
        form = WarrantyClaimEntryForm(request.POST)
        if form.is_valid():
            claim = form.save()
            log_activity(request, ActivityLog.Area.WARRANTY, claim.job_number, "Warranty claim logged", claim.report_warranty_claimed[:255])
            messages.success(request, f"Warranty claim {claim.job_number} logged.")
            return redirect("warranty_detail", pk=claim.pk)
    else:
        form = WarrantyClaimEntryForm(initial={"date_in": date.today()})
    return render(request, "service/warranty_form.html", {"form": form, "mode": "entry"})


@login_required
def warranty_exit(request, pk):
    """Exit form — auto-fills entry details in the template."""
    claim = get_object_or_404(WarrantyClaim, pk=pk)
    if request.method == "POST":
        form = WarrantyClaimExitForm(request.POST, instance=claim)
        if form.is_valid():
            form.save()
            log_activity(request, ActivityLog.Area.WARRANTY, claim.job_number, "Warranty exit updated", claim.not_solved_cause[:255])
            messages.success(request, f"Warranty claim {claim.job_number} updated.")
            return redirect("warranty_detail", pk=claim.pk)
    else:
        initial = {"sent_date_out": date.today()} if not claim.sent_date_out else {}
        form = WarrantyClaimExitForm(instance=claim, initial=initial)
    return render(request, "service/warranty_form.html", {"form": form, "mode": "exit", "claim": claim})


@login_required
def warranty_detail(request, pk):
    claim = get_object_or_404(WarrantyClaim.objects.select_related("sold_to", "machine"), pk=pk)
    return render(request, "service/warranty_detail.html", {"claim": claim})


@login_required
def warranty_export_pdf(request, pk):
    claim = get_object_or_404(WarrantyClaim.objects.select_related("sold_to", "machine"), pk=pk)
    rows = [
        ("Job Number", claim.job_number),
        ("Date In", claim.date_in),
        ("Received By", claim.received_by),
        ("Sold To", claim.sold_to.name),
        ("Company", claim.sold_to.company_name),
        ("Bought From", claim.bought_from),
        ("Machine", f"{claim.machine.machine_type} — {claim.machine.brand} {claim.machine.model_name}"),
        ("Serial Number", claim.machine.serial_number),
        ("Warranty Sent Date", claim.warranty_sent_date),
        ("Claimable", claim.get_claimable_display() if claim.claimable else ""),
        ("Warranty Claimed Report", claim.report_warranty_claimed),
        ("Solved", claim.get_solved_display() if claim.solved else ""),
        ("Cause (if not solved)", claim.not_solved_cause),
        ("Sent Date (Exit)", claim.sent_date_out),
        ("Report Complete", "Yes" if claim.report_complete else "No"),
    ]
    return build_report_pdf(
        filename=f"warranty_{claim.job_number}.pdf",
        title="Warranty Claim Report",
        subtitle=f"Generated on {date.today()}",
        field_rows=rows,
    )

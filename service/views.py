import calendar
from datetime import date, datetime, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from .forms import (
    ClientForm, MachineForm, RepairJobEntryForm, RepairJobExitForm,
    WarrantyClaimEntryForm, WarrantyClaimExitForm,
)
from .models import ActivityLog, Client, Machine, RepairJob, WarrantyClaim
from .pdf_utils import build_report_pdf

MANAGEMENT_GROUP = "Management"
REPAIR_GROUP    = "Repair Desk"
WARRANTY_GROUP  = "Warranty Desk"


def is_management_user(user):
    """Management group members receive the reporting-only area."""
    return user.is_authenticated and user.groups.filter(name=MANAGEMENT_GROUP).exists()


def is_repair_staff(user):
    """True for Repair Desk, Management, and superusers."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=[REPAIR_GROUP, MANAGEMENT_GROUP]).exists()


def is_warranty_staff(user):
    """True for Warranty Desk, Management, and superusers."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=[WARRANTY_GROUP, MANAGEMENT_GROUP]).exists()


def helpdesk_required(view_func):
    """Keep reporting-only management accounts out of ticket screens."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if is_management_user(request.user):
            return redirect("management_dashboard")
        return view_func(request, *args, **kwargs)
    return wrapped_view


def repair_required(view_func):
    """Restrict view to Repair Desk staff (or Management/Superuser)."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not is_repair_staff(request.user):
            return HttpResponseForbidden(
                "You do not have access to Repair Jobs. "
                "Please contact your administrator."
            )
        return view_func(request, *args, **kwargs)
    return wrapped_view


def warranty_required(view_func):
    """Restrict view to Warranty Desk staff (or Management/Superuser)."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not is_warranty_staff(request.user):
            return HttpResponseForbidden(
                "You do not have access to Warranty Claims. "
                "Please contact your administrator."
            )
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
        user = self.request.user

        if is_management_user(user):
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
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            if is_ajax:
                return JsonResponse({"status": "success", "id": client.pk, "name": str(client)})
            messages.success(request, f"Client '{client.name}' added.")
            return redirect(_safe_next(request, "repair_create"))
        else:
            if is_ajax:
                html = render_to_string("service/quick_form_partial.html", {
                    "form": form, "title": "New Client",
                }, request=request)
                return JsonResponse({"status": "error", "html": html})
    else:
        form = ClientForm()
    
    if is_ajax:
        html = render_to_string("service/quick_form_partial.html", {
            "form": form, "title": "New Client",
        }, request=request)
        return JsonResponse({"status": "success", "html": html})
        
    return render(request, "service/quick_form.html", {
        "form": form, "title": "New Client",
        "next": request.GET.get("next", ""),
    })


@login_required
def machine_create(request):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    client_id = request.GET.get("client_id") or request.POST.get("client")
    if request.method == "POST":
        form = MachineForm(request.POST)
        if form.is_valid():
            machine = form.save()
            if is_ajax:
                return JsonResponse({
                    "status": "success",
                    "id": machine.pk,
                    "name": str(machine),
                    "client_id": machine.client.id
                })
            messages.success(request, f"Machine added for {machine.client.name}.")
            return redirect(_safe_next(request, "repair_create"))
        else:
            if is_ajax:
                html = render_to_string("service/quick_form_partial.html", {
                    "form": form, "title": "New Machine",
                }, request=request)
                return JsonResponse({"status": "error", "html": html})
    else:
        initial = {}
        if client_id:
            initial["client"] = client_id
        form = MachineForm(initial=initial)
        
    if is_ajax:
        html = render_to_string("service/quick_form_partial.html", {
            "form": form, "title": "New Machine",
        }, request=request)
        return JsonResponse({"status": "success", "html": html})
        
    return render(request, "service/quick_form.html", {
        "form": form, "title": "New Machine",
        "next": request.GET.get("next", ""),
    })


# ---------------------------------------------------------------------------
# RMS (Repair) workflow
# ---------------------------------------------------------------------------
# Client Directory & Client Wise Details (Accessible to both Admin & Staff)
# ---------------------------------------------------------------------------

@login_required
def client_list(request):
    """Client Directory view accessible by both Admin and Staff."""
    from django.db.models import Q, Count
    query = request.GET.get("q", "").strip()
    clients = Client.objects.annotate(
        machines_count=Count("machines", distinct=True),
        repairs_count=Count("repair_jobs", distinct=True),
        claims_count=Count("warranty_claims", distinct=True),
    )
    if query:
        clients = clients.filter(
            Q(name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(address__icontains=query)
        )
    clients = clients.order_by("name")
    paginator = Paginator(clients, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "service/client_list.html", {
        "clients": page_obj,
        "page_obj": page_obj,
        "query": query,
    })


@login_required
def client_detail(request, pk):
    """Client Wise Details view showing profile, stats, machines, repair jobs, and warranty claims."""
    client = get_object_or_404(Client, pk=pk)
    machines = client.machines.all()
    repair_jobs = client.repair_jobs.select_related("machine").order_by("-created_at")
    warranty_claims = client.warranty_claims.select_related("machine").order_by("-created_at")

    # Client-specific stats
    total_repairs = repair_jobs.count()
    pending_repairs = repair_jobs.filter(status=RepairJob.Status.PENDING).count()
    completed_repairs = repair_jobs.filter(status=RepairJob.Status.COMPLETED).count()
    total_claims = warranty_claims.count()
    open_claims = warranty_claims.filter(solved="").count()

    return render(request, "service/client_detail.html", {
        "client": client,
        "machines": machines,
        "repair_jobs": repair_jobs,
        "warranty_claims": warranty_claims,
        "total_repairs": total_repairs,
        "pending_repairs": pending_repairs,
        "completed_repairs": completed_repairs,
        "total_claims": total_claims,
        "open_claims": open_claims,
    })


# ---------------------------------------------------------------------------
# RMS (Repair) workflow
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    """Operational overview for staff at the start of a service-desk shift."""
    user = request.user
    can_repair   = is_repair_staff(user)
    can_warranty = is_warranty_staff(user)

    repairs = RepairJob.objects.select_related("client", "machine") if can_repair else RepairJob.objects.none()
    claims  = WarrantyClaim.objects.select_related("sold_to", "machine") if can_warranty else WarrantyClaim.objects.none()

    client_id = request.GET.get("client_id")
    selected_client = None
    if client_id and client_id.isdigit():
        selected_client = Client.objects.filter(pk=client_id).first()
        if selected_client:
            repairs = repairs.filter(client=selected_client)
            claims  = claims.filter(sold_to=selected_client)

    three_days_ago = date.today() - timedelta(days=3)
    delayed_repairs = RepairJob.objects.none()
    if can_repair:
        delayed_repairs = RepairJob.objects.filter(
            status=RepairJob.Status.PENDING,
            date_in__lte=three_days_ago
        )
        if selected_client:
            delayed_repairs = delayed_repairs.filter(client=selected_client)
        delayed_repairs = delayed_repairs.select_related("client", "machine")

    clients = Client.objects.all()

    return render(request, "service/dashboard.html", {
        "client_count": Client.objects.count(),
        "machine_count": Machine.objects.count(),
        "repair_total":   repairs.count(),
        "repair_pending":  repairs.filter(status=RepairJob.Status.PENDING).count(),
        "claim_total":    claims.count(),
        "claim_open":     claims.filter(solved="").count(),
        "claim_review":   claims.filter(claimable="").count(),
        "recent_repairs": repairs[:5],
        "recent_claims":  claims[:5],
        "delayed_repairs": delayed_repairs,
        "clients": clients,
        "selected_client": selected_client,
        "client_id": int(client_id) if client_id and client_id.isdigit() else None,
    })


@management_required
def management_dashboard(request):
    """Read-only KPI overview for management users with Monthly and Client filters."""
    import json
    from django.db.models import Count

    today = date.today()
    selected_month = request.GET.get("month", "").strip()
    client_id = request.GET.get("client_id", "").strip()

    if not selected_month:
        selected_month = today.strftime("%Y-%m")

    # Base querysets
    repairs = RepairJob.objects.select_related("client", "machine")
    claims = WarrantyClaim.objects.select_related("sold_to", "machine")

    selected_client = None
    if client_id and client_id.isdigit():
        selected_client = Client.objects.filter(pk=client_id).first()
        if selected_client:
            repairs = repairs.filter(client=selected_client)
            claims = claims.filter(sold_to=selected_client)

    is_all_time = (selected_month == "all")
    if is_all_time:
        month_label = "All Time"
        month_start = None
        month_end = None

        repairs_received_month = repairs.count()
        completed_this_month = repairs.filter(status=RepairJob.Status.COMPLETED)
        claims_received_month = claims.count()
        claims_claimable_month = claims.filter(claimable=WarrantyClaim.Claimable.YES).count()
    else:
        try:
            dt = datetime.strptime(selected_month, "%Y-%m").date()
            year, month_num = dt.year, dt.month
        except (ValueError, TypeError):
            dt = today
            year, month_num = today.year, today.month
            selected_month = today.strftime("%Y-%m")
        
        last_day = calendar.monthrange(year, month_num)[1]
        month_start = date(year, month_num, 1)
        month_end = date(year, month_num, last_day)
        month_label = month_start.strftime("%B %Y")

        repairs_received_month = repairs.filter(date_in__gte=month_start, date_in__lte=month_end).count()
        completed_this_month = repairs.filter(
            status=RepairJob.Status.COMPLETED,
            date_out__gte=month_start,
            date_out__lte=month_end,
        )
        claims_received_month = claims.filter(date_in__gte=month_start, date_in__lte=month_end).count()
        claims_claimable_month = claims.filter(
            date_in__gte=month_start,
            date_in__lte=month_end,
            claimable=WarrantyClaim.Claimable.YES,
        ).count()

    repairs_completed_month = completed_this_month.count()
    completion_rate = int((repairs_completed_month / repairs_received_month) * 100) if repairs_received_month > 0 else 0

    turnaround_days = [
        (job.date_out - job.date_in).days
        for job in completed_this_month
        if job.date_out and job.date_in
    ]

    three_days_ago = today - timedelta(days=3)
    delayed_repairs = repairs.filter(
        status=RepairJob.Status.PENDING,
        date_in__lte=three_days_ago
    )

    # Intakes Trend Chart data
    chart_days = []
    chart_repairs = []
    chart_claims = []

    if not is_all_time and month_start and month_end:
        cur = month_start
        while cur <= month_end:
            chart_days.append(cur.strftime("%d %b"))
            chart_repairs.append(repairs.filter(date_in=cur).count())
            chart_claims.append(claims.filter(date_in=cur).count())
            cur += timedelta(days=1)
    else:
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            chart_days.append(day.strftime("%b %d"))
            chart_repairs.append(repairs.filter(date_in=day).count())
            chart_claims.append(claims.filter(date_in=day).count())

    # Asset breakdown
    if selected_client:
        machine_types_qs = Machine.objects.filter(client=selected_client)
    else:
        machine_types_qs = Machine.objects.all()
    machine_types_data = list(machine_types_qs.values('machine_type').annotate(count=Count('id')).order_by('-count')[:5])
    chart_machine_types = [item['machine_type'] for item in machine_types_data]
    chart_machine_counts = [item['count'] for item in machine_types_data]

    chart_json = json.dumps({
        "labels": chart_days,
        "repairs": chart_repairs,
        "claims": chart_claims,
        "machine_labels": chart_machine_types,
        "machine_counts": chart_machine_counts,
    })

    # Available months list for dropdown selector (past 12 months)
    available_months = []
    curr_m = today.replace(day=1)
    for _ in range(12):
        m_str = curr_m.strftime("%Y-%m")
        m_lbl = curr_m.strftime("%B %Y")
        available_months.append({"value": m_str, "label": m_lbl})
        prev_m_end = curr_m - timedelta(days=1)
        curr_m = prev_m_end.replace(day=1)

    clients = Client.objects.all()

    return render(request, "service/management_dashboard.html", {
        "selected_month": selected_month,
        "month_label": month_label,
        "month_start": month_start,
        "today": today,
        "selected_client": selected_client,
        "client_id": int(client_id) if client_id and client_id.isdigit() else None,
        "clients": clients,
        "available_months": available_months,
        "repairs_received_month": repairs_received_month,
        "repairs_completed_month": repairs_completed_month,
        "repair_backlog": repairs.filter(status=RepairJob.Status.PENDING).count(),
        "completion_rate": completion_rate,
        "average_turnaround": round(sum(turnaround_days) / len(turnaround_days), 1) if turnaround_days else None,
        "claims_received_month": claims_received_month,
        "claims_claimable_month": claims_claimable_month,
        "claims_open": claims.filter(solved="").count(),
        "repairs_last_30_days": repairs.filter(date_in__gte=today - timedelta(days=30)).count(),
        "claims_last_30_days": claims.filter(date_in__gte=today - timedelta(days=30)).count(),
        "recent_logs": ActivityLog.objects.select_related("actor")[:6],
        "delayed_repairs": delayed_repairs,
        "chart_json": chart_json,
    })


@management_required
def management_logs(request):
    logs_qs = ActivityLog.objects.select_related("actor")
    paginator = Paginator(logs_qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "service/management_logs.html", {
        "logs": page_obj,
        "page_obj": page_obj,
    })


@repair_required
def repair_list(request):
    jobs = RepairJob.objects.select_related("client", "machine")
    status = request.GET.get("status", "").strip()
    client_id = request.GET.get("client_id", "").strip()
    serial_number = request.GET.get("serial_number", "").strip()
    date_in = request.GET.get("date_in", "").strip()

    if status in ("pending", "completed"):
        jobs = jobs.filter(status=status)
    if client_id and client_id.isdigit():
        jobs = jobs.filter(client_id=client_id)
    if serial_number:
        jobs = jobs.filter(machine__serial_number__icontains=serial_number)
    if date_in:
        jobs = jobs.filter(date_in=date_in)

    paginator = Paginator(jobs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    clients = Client.objects.all()
    has_filters = bool(status or client_id or serial_number or date_in)

    return render(request, "service/repair_list.html", {
        "jobs": page_obj,
        "page_obj": page_obj,
        "status": status,
        "client_id": int(client_id) if client_id and client_id.isdigit() else None,
        "serial_number": serial_number,
        "date_in": date_in,
        "clients": clients,
        "has_filters": has_filters,
    })


@repair_required
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


@repair_required
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


@repair_required
def repair_detail(request, pk):
    job = get_object_or_404(RepairJob.objects.select_related("client", "machine"), pk=pk)
    return render(request, "service/repair_detail.html", {"job": job})


@repair_required
def repair_export_pdf(request, pk):
    from .nepali_date import ad_to_bs_display
    job = get_object_or_404(RepairJob.objects.select_related("client", "machine"), pk=pk)
    rows = [
        ("Job Number", job.job_number),
        ("Status", job.get_status_display()),
        ("Date In", job.date_in_bs),
        ("Client", job.client.name),
        ("Company", job.client.company_name),
        ("Received By", job.received_by),
        ("Machine", f"{job.machine.machine_type} — {job.machine.brand} {job.machine.model_name}"),
        ("Serial Number", job.machine.serial_number),
        ("Problem / Cause", job.problem_cause),
        ("Date Out", job.date_out_bs),
        ("Repaired By", job.repaired_by),
        ("Challan Number", job.challan_number),
        ("Solution / Repair Detail", job.solution_detail),
        ("Taken By", job.taken_by),
    ]
    return build_report_pdf(
        filename=f"repair_{job.job_number}.pdf",
        title="RMS — Repair Job Report",
        subtitle=f"Generated on {ad_to_bs_display(date.today())}",
        field_rows=rows,
    )


# ---------------------------------------------------------------------------
# Warranty workflow
# ---------------------------------------------------------------------------

@warranty_required
def warranty_list(request):
    claims = WarrantyClaim.objects.select_related("sold_to", "machine")
    claimable = request.GET.get("claimable", "").strip()
    client_id = request.GET.get("client_id", "").strip()

    if claimable == "yes":
        claims = claims.filter(claimable=WarrantyClaim.Claimable.YES)
    elif claimable == "no":
        claims = claims.filter(claimable=WarrantyClaim.Claimable.NO)
    elif claimable == "pending":
        claims = claims.filter(claimable="")

    if client_id and client_id.isdigit():
        claims = claims.filter(sold_to_id=client_id)

    paginator = Paginator(claims, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    clients = Client.objects.all()
    has_filters = bool(claimable or client_id)

    return render(request, "service/warranty_list.html", {
        "claims": page_obj,
        "page_obj": page_obj,
        "claimable": claimable,
        "client_id": int(client_id) if client_id and client_id.isdigit() else None,
        "clients": clients,
        "has_filters": has_filters,
    })


@warranty_required
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


@warranty_required
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


@warranty_required
def warranty_detail(request, pk):
    claim = get_object_or_404(WarrantyClaim.objects.select_related("sold_to", "machine"), pk=pk)
    return render(request, "service/warranty_detail.html", {"claim": claim})


@warranty_required
def warranty_export_pdf(request, pk):
    from .nepali_date import ad_to_bs_display
    claim = get_object_or_404(WarrantyClaim.objects.select_related("sold_to", "machine"), pk=pk)
    rows = [
        ("Job Number", claim.job_number),
        ("Date In", claim.date_in_bs),
        ("Received By", claim.received_by),
        ("Sold To", claim.sold_to.name),
        ("Company", claim.sold_to.company_name),
        ("Bought From", claim.bought_from),
        ("Machine", f"{claim.machine.machine_type} — {claim.machine.brand} {claim.machine.model_name}"),
        ("Serial Number", claim.machine.serial_number),
        ("Warranty Sent Date", claim.warranty_sent_date_bs),
        ("Claimable", claim.get_claimable_display() if claim.claimable else ""),
        ("Warranty Claimed Report", claim.report_warranty_claimed),
        ("Solved", claim.get_solved_display() if claim.solved else ""),
        ("Cause (if not solved)", claim.not_solved_cause),
        ("Sent Date (Exit)", claim.sent_date_out_bs),
        ("Report Complete", "Yes" if claim.report_complete else "No"),
    ]
    return build_report_pdf(
        filename=f"warranty_{claim.job_number}.pdf",
        title="Warranty Claim Report",
        subtitle=f"Generated on {ad_to_bs_display(date.today())}",
        field_rows=rows,
    )


@login_required
def global_search(request):
    from django.db.models import Q
    query = request.GET.get("q", "").strip()
    clients  = []
    machines = []
    repairs  = []
    claims   = []

    if query:
        clients = Client.objects.filter(
            Q(name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(phone__icontains=query)
        )
        machines = Machine.objects.filter(
            Q(machine_type__icontains=query) |
            Q(brand__icontains=query) |
            Q(model_name__icontains=query) |
            Q(serial_number__icontains=query)
        ).select_related("client")
        if is_repair_staff(request.user):
            repairs = RepairJob.objects.filter(
                Q(job_number__icontains=query) |
                Q(problem_cause__icontains=query) |
                Q(client__name__icontains=query) |
                Q(received_by__icontains=query)
            ).select_related("client", "machine")
        if is_warranty_staff(request.user):
            claims = WarrantyClaim.objects.filter(
                Q(job_number__icontains=query) |
                Q(sold_to__name__icontains=query) |
                Q(bought_from__icontains=query) |
                Q(received_by__icontains=query)
            ).select_related("sold_to", "machine")

    return render(request, "service/search_results.html", {
        "query": query,
        "clients":  clients,
        "machines": machines,
        "repairs":  repairs,
        "claims":   claims,
    })


@repair_required
def repair_receipt(request, pk):
    job = get_object_or_404(RepairJob.objects.select_related("client", "machine"), pk=pk)
    return render(request, "service/repair_receipt.html", {"job": job})


@warranty_required
def warranty_receipt(request, pk):
    claim = get_object_or_404(WarrantyClaim.objects.select_related("sold_to", "machine"), pk=pk)
    return render(request, "service/warranty_receipt.html", {"claim": claim})

from django.contrib import admin

from .models import ActivityLog, Client, Machine, RepairJob, WarrantyClaim


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "company_name", "phone")
    search_fields = ("name", "company_name", "phone")


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("machine_type", "brand", "model_name", "serial_number", "client")
    search_fields = ("brand", "model_name", "serial_number", "client__name")
    list_filter = ("machine_type", "brand")


@admin.register(RepairJob)
class RepairJobAdmin(admin.ModelAdmin):
    list_display = ("job_number", "client", "machine", "status", "date_in", "date_out")
    list_filter = ("status",)
    search_fields = ("job_number", "client__name", "machine__serial_number")
    readonly_fields = ("job_number",)


@admin.register(WarrantyClaim)
class WarrantyClaimAdmin(admin.ModelAdmin):
    list_display = ("job_number", "sold_to", "machine", "claimable", "solved", "date_in")
    list_filter = ("claimable", "solved", "report_complete")
    search_fields = ("job_number", "sold_to__name", "machine__serial_number")
    readonly_fields = ("job_number",)

admin.site.register(ActivityLog)
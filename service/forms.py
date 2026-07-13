from django import forms

from .models import Client, Machine, RepairJob, WarrantyClaim


# ---------------------------------------------------------------------------
# Shared client/machine quick-create
# ---------------------------------------------------------------------------

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "company_name", "phone", "address"]


class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ["client", "machine_type", "brand", "model_name", "serial_number", "details"]
        widgets = {
            "details": forms.Textarea(attrs={"rows": 3}),
        }


# ---------------------------------------------------------------------------
# RMS
# ---------------------------------------------------------------------------

class RepairJobEntryForm(forms.ModelForm):
    class Meta:
        model = RepairJob
        fields = ["date_in", "client", "received_by", "machine", "problem_cause"]
        widgets = {
            "date_in": forms.DateInput(attrs={"type": "date"}),
            "problem_cause": forms.Textarea(attrs={"rows": 4}),
        }


class RepairJobExitForm(forms.ModelForm):
    class Meta:
        model = RepairJob
        fields = ["date_out", "solution_detail", "taken_by", "status"]
        widgets = {
            "date_out": forms.DateInput(attrs={"type": "date"}),
            "solution_detail": forms.Textarea(attrs={"rows": 4}),
        }


# ---------------------------------------------------------------------------
# Warranty
# ---------------------------------------------------------------------------

class WarrantyClaimEntryForm(forms.ModelForm):
    class Meta:
        model = WarrantyClaim
        fields = [
            "date_in", "received_by", "sold_to", "bought_from", "machine",
            "warranty_sent_date", "claimable", "report_warranty_claimed",
        ]
        widgets = {
            "date_in": forms.DateInput(attrs={"type": "date"}),
            "warranty_sent_date": forms.DateInput(attrs={"type": "date"}),
            "report_warranty_claimed": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("claimable") == "yes" and not cleaned.get("report_warranty_claimed"):
            self.add_error("report_warranty_claimed", "Please describe the warranty claim.")
        return cleaned


class WarrantyClaimExitForm(forms.ModelForm):
    class Meta:
        model = WarrantyClaim
        fields = ["solved", "not_solved_cause", "sent_date_out", "report_complete"]
        widgets = {
            "sent_date_out": forms.DateInput(attrs={"type": "date"}),
            "not_solved_cause": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("solved") == "not_solved" and not cleaned.get("not_solved_cause"):
            self.add_error("not_solved_cause", "Please state the cause since it wasn't solved.")
        return cleaned

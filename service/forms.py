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

    def clean(self):
        cleaned = super().clean()
        client = cleaned.get("client")
        machine = cleaned.get("machine")
        if client and machine and machine.client_id != client.id:
            self.add_error("machine", "Choose a machine registered to the selected client.")
        return cleaned


class RepairJobExitForm(forms.ModelForm):
    class Meta:
        model = RepairJob
        fields = ["date_out", "solution_detail", "taken_by", "status"]
        widgets = {
            "date_out": forms.DateInput(attrs={"type": "date"}),
            "solution_detail": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        date_out = cleaned.get("date_out")
        status = cleaned.get("status")
        solution_detail = cleaned.get("solution_detail")
        taken_by = cleaned.get("taken_by")

        if date_out and self.instance.date_in and date_out < self.instance.date_in:
            self.add_error("date_out", "Date out cannot be before the intake date.")
        if status == RepairJob.Status.COMPLETED:
            if not date_out:
                self.add_error("date_out", "A completed job needs a date out.")
            if not solution_detail:
                self.add_error("solution_detail", "Describe the repair or resolution before completing the job.")
            if not taken_by:
                self.add_error("taken_by", "Record who collected the machine before completing the job.")
        return cleaned


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
        client = cleaned.get("sold_to")
        machine = cleaned.get("machine")
        if client and machine and machine.client_id != client.id:
            self.add_error("machine", "Choose a machine registered to the selected client.")
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
        sent_date_out = cleaned.get("sent_date_out")
        solved = cleaned.get("solved")
        if sent_date_out and self.instance.date_in and sent_date_out < self.instance.date_in:
            self.add_error("sent_date_out", "Sent date cannot be before the intake date.")
        if solved and not sent_date_out:
            self.add_error("sent_date_out", "Provide the sent date when closing the claim.")
        if cleaned.get("solved") == "not_solved" and not cleaned.get("not_solved_cause"):
            self.add_error("not_solved_cause", "Please state the cause since it wasn't solved.")
        return cleaned

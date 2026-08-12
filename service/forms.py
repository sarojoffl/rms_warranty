from django import forms

from .models import Client, Machine, RepairJob, WarrantyClaim


# ---------------------------------------------------------------------------
# Shared client/machine quick-create
# ---------------------------------------------------------------------------

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["company_name", "name", "phone", "address"]
        labels = {
            "company_name": "Company Name",
            "name": "Contact Person",
        }
        help_texts = {
            "company_name": "Fill in the company name, contact person, or both.",
            "name": "",
        }

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("name", "").strip()
        company_name = cleaned.get("company_name", "").strip()
        if not name and not company_name:
            raise forms.ValidationError(
                "Please fill in at least a Company Name or a Contact Person."
            )
        return cleaned


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
        fields = ["date_out", "repaired_by", "challan_number", "solution_detail", "taken_by", "status"]
        widgets = {
            "date_out": forms.DateInput(attrs={"type": "date"}),
            "solution_detail": forms.Textarea(attrs={"rows": 4}),
            "challan_number": forms.TextInput(attrs={"placeholder": "e.g. CH-2081-0042"}),
            "repaired_by": forms.TextInput(attrs={"placeholder": "Technician name"}),
        }
        labels = {
            "challan_number": "Challan Number",
            "repaired_by": "Repaired By",
            "solution_detail": "Solution / Repair Detail",
        }

    def clean(self):
        cleaned = super().clean()
        date_out = cleaned.get("date_out")
        status = cleaned.get("status")
        solution_detail = cleaned.get("solution_detail", "").strip()
        taken_by = cleaned.get("taken_by", "").strip()
        challan_number = cleaned.get("challan_number", "").strip()
        repaired_by = cleaned.get("repaired_by", "").strip()

        if date_out and self.instance.date_in and date_out < self.instance.date_in:
            self.add_error("date_out", "Date out cannot be before the intake date.")

        if status == RepairJob.Status.COMPLETED:
            if not date_out:
                self.add_error("date_out", "A completed job needs a date out.")
            if not repaired_by:
                self.add_error("repaired_by", "Repaired By is required to complete the job.")
            if not solution_detail:
                self.add_error("solution_detail", "Solution / Repair Detail is required to complete the job.")
            if not taken_by:
                self.add_error("taken_by", "Record who collected the machine before completing the job.")
            if not challan_number:
                self.add_error("challan_number", "Challan number is required before the item can be exited.")
        return cleaned


# ---------------------------------------------------------------------------
# Warranty
# ---------------------------------------------------------------------------

class WarrantyClaimEntryForm(forms.ModelForm):
    class Meta:
        model = WarrantyClaim
        fields = [
            "date_in", "received_by", "sold_to", "bought_from", "machine",
            "warranty_sent_date", "delivered_by", "claimable", "report_warranty_claimed",
        ]
        widgets = {
            "date_in": forms.DateInput(attrs={"type": "date"}),
            "warranty_sent_date": forms.DateInput(attrs={"type": "date"}),
            "report_warranty_claimed": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "delivered_by": "Delivered By (to distributor)",
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
        fields = ["solved", "not_solved_cause", "sent_date_out", "taken_by", "report_complete"]
        widgets = {
            "sent_date_out": forms.DateInput(attrs={"type": "date"}),
            "not_solved_cause": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "taken_by": "Taken By (customer pickup)",
        }

    def clean(self):
        cleaned = super().clean()
        sent_date_out = cleaned.get("sent_date_out")
        solved = cleaned.get("solved")
        taken_by = cleaned.get("taken_by", "").strip()
        if sent_date_out and self.instance.date_in and sent_date_out < self.instance.date_in:
            self.add_error("sent_date_out", "Sent date cannot be before the intake date.")
        if solved and not sent_date_out:
            self.add_error("sent_date_out", "Provide the sent date when closing the claim.")
        if cleaned.get("solved") == "not_solved" and not cleaned.get("not_solved_cause"):
            self.add_error("not_solved_cause", "Please state the cause since it wasn't solved.")
        if solved and not taken_by:
            self.add_error("taken_by", "Record who collected the machine before closing the claim.")
        return cleaned


# ---------------------------------------------------------------------------
# Edit forms
# ---------------------------------------------------------------------------

class RepairJobEditForm(forms.ModelForm):
    class Meta:
        model = RepairJob
        fields = [
            "date_in", "client", "received_by", "machine", "problem_cause",
            "status", "date_out", "repaired_by", "challan_number", "solution_detail", "taken_by",
        ]
        widgets = {
            "date_in": forms.DateInput(attrs={"type": "date"}),
            "date_out": forms.DateInput(attrs={"type": "date"}),
            "problem_cause": forms.Textarea(attrs={"rows": 3}),
            "solution_detail": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "problem_cause": "Problem / Cause",
            "solution_detail": "Solution / Repair Detail",
            "challan_number": "Challan Number",
            "repaired_by": "Repaired By",
        }

    EXIT_FIELDS = ["date_out", "repaired_by", "challan_number", "solution_detail", "taken_by"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_exited = bool(self.instance and self.instance.pk and self.instance.date_out)
        if not self.is_exited:
            for name in self.EXIT_FIELDS:
                del self.fields[name]
            self.fields["status"].disabled = True

    def clean(self):
        cleaned = super().clean()
        if not self.is_exited:
            return cleaned

        date_in = cleaned.get("date_in")
        date_out = cleaned.get("date_out")
        status = cleaned.get("status")
        if date_in and date_out and date_out < date_in:
            self.add_error("date_out", "Date out cannot be before the intake date.")
        if status == RepairJob.Status.COMPLETED:
            if not date_out:
                self.add_error("date_out", "A completed job needs a date out.")
            if not cleaned.get("repaired_by", "").strip():
                self.add_error("repaired_by", "Repaired By is required to complete the job.")
            if not cleaned.get("solution_detail", "").strip():
                self.add_error("solution_detail", "Solution / Repair Detail is required to complete the job.")
            if not cleaned.get("taken_by", "").strip():
                self.add_error("taken_by", "Record who collected the machine before completing the job.")
            if not cleaned.get("challan_number", "").strip():
                self.add_error("challan_number", "Challan number is required before the item can be exited.")
        return cleaned


class WarrantyClaimEditForm(forms.ModelForm):
    class Meta:
        model = WarrantyClaim
        fields = [
            "date_in", "received_by", "sold_to", "bought_from", "machine",
            "warranty_sent_date", "delivered_by", "claimable", "report_warranty_claimed",
            "solved", "not_solved_cause", "sent_date_out", "taken_by", "report_complete",
        ]
        widgets = {
            "date_in": forms.DateInput(attrs={"type": "date"}),
            "warranty_sent_date": forms.DateInput(attrs={"type": "date"}),
            "sent_date_out": forms.DateInput(attrs={"type": "date"}),
            "report_warranty_claimed": forms.Textarea(attrs={"rows": 3}),
            "not_solved_cause": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "delivered_by": "Delivered By (to distributor)",
            "taken_by": "Taken By (customer pickup)",
        }

    EXIT_FIELDS = ["solved", "not_solved_cause", "sent_date_out", "taken_by", "report_complete"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_exited = bool(self.instance and self.instance.pk and self.instance.sent_date_out)
        if not self.is_exited:
            for name in self.EXIT_FIELDS:
                del self.fields[name]

    def clean(self):
        cleaned = super().clean()
        if not self.is_exited:
            return cleaned

        date_in = cleaned.get("date_in")
        sent_date_out = cleaned.get("sent_date_out")
        solved = cleaned.get("solved")
        if date_in and sent_date_out and sent_date_out < date_in:
            self.add_error("sent_date_out", "Sent date cannot be before the intake date.")
        if solved and not sent_date_out:
            self.add_error("sent_date_out", "Provide the sent date when closing the claim.")
        if cleaned.get("solved") == "not_solved" and not cleaned.get("not_solved_cause"):
            self.add_error("not_solved_cause", "Please state the cause since it wasn't solved.")
        if cleaned.get("claimable") == "yes" and not cleaned.get("report_warranty_claimed"):
            self.add_error("report_warranty_claimed", "Please describe the warranty claim.")
        return cleaned
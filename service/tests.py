from datetime import date, timedelta

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from .forms import (
    RepairJobEntryForm,
    RepairJobExitForm,
    WarrantyClaimEntryForm,
    WarrantyClaimExitForm,
)
from .models import Client, Machine, RepairJob, WarrantyClaim


class TicketFormValidationTests(TestCase):
    def setUp(self):
        self.client_a = Client.objects.create(name="Asha")
        self.client_b = Client.objects.create(name="Bikash")
        self.machine = Machine.objects.create(
            client=self.client_a,
            machine_type="Laptop",
            serial_number="SN-100",
        )

    def test_repair_intake_requires_a_machine_owned_by_the_selected_client(self):
        form = RepairJobEntryForm(data={
            "date_in": date.today(),
            "client": self.client_b.pk,
            "received_by": "Asha",
            "machine": self.machine.pk,
            "problem_cause": "Will not power on",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("machine", form.errors)

    def test_completed_repair_requires_handover_information(self):
        job = RepairJob.objects.create(
            date_in=date.today(), client=self.client_a, received_by="Asha",
            machine=self.machine, problem_cause="Will not power on",
        )
        form = RepairJobExitForm(data={
            "date_out": "",
            "solution_detail": "",
            "taken_by": "",
            "challan_number": "",
            "repaired_by": "",
            "status": RepairJob.Status.COMPLETED,
        }, instance=job)
        self.assertFalse(form.is_valid())
        self.assertIn("date_out", form.errors)
        self.assertIn("solution_detail", form.errors)
        self.assertIn("taken_by", form.errors)
        self.assertIn("challan_number", form.errors)
        self.assertIn("repaired_by", form.errors)

    def test_repair_exit_date_cannot_precede_intake(self):
        job = RepairJob.objects.create(
            date_in=date.today(), client=self.client_a, received_by="Asha",
            machine=self.machine, problem_cause="Will not power on",
        )
        form = RepairJobExitForm(data={
            "date_out": date.today() - timedelta(days=1),
            "solution_detail": "Replaced power supply",
            "taken_by": "Asha",
            "repaired_by": "Rohan",
            "challan_number": "CH-123",
            "status": RepairJob.Status.COMPLETED,
        }, instance=job)
        self.assertFalse(form.is_valid())
        self.assertIn("date_out", form.errors)

    def test_warranty_intake_requires_a_machine_owned_by_the_selected_client(self):
        form = WarrantyClaimEntryForm(data={
            "date_in": date.today(),
            "received_by": "Asha",
            "sold_to": self.client_b.pk,
            "machine": self.machine.pk,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("machine", form.errors)

    def test_warranty_exit_date_cannot_precede_intake(self):
        claim = WarrantyClaim.objects.create(
            date_in=date.today(), received_by="Asha", sold_to=self.client_a,
            machine=self.machine,
        )
        form = WarrantyClaimExitForm(data={
            "solved": WarrantyClaim.RepairStatus.SOLVED,
            "sent_date_out": date.today() - timedelta(days=1),
            "report_complete": True,
        }, instance=claim)
        self.assertFalse(form.is_valid())
        self.assertIn("sent_date_out", form.errors)

    def test_machine_options_only_returns_the_selected_clients_machines(self):
        other_machine = Machine.objects.create(client=self.client_b, machine_type="Printer")
        user = get_user_model().objects.create_user(username="staff", password="test-password")
        self.client.force_login(user)

        response = self.client.get(reverse("machine_options"), {"client_id": self.client_a.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["machines"], [{"id": self.machine.pk, "label": str(self.machine)}])
        self.assertNotIn(other_machine.pk, [item["id"] for item in response.json()["machines"]])

    @override_settings(
        STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
    )
    def test_dashboard_requires_login_and_shows_operational_counts(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('dashboard')}",
            fetch_redirect_response=False,
        )

        RepairJob.objects.create(
            date_in=date.today(), client=self.client_a, received_by="Asha",
            machine=self.machine, problem_cause="Will not power on",
        )
        user = get_user_model().objects.create_user(username="manager", password="test-password")
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Operations Dashboard")
        self.assertEqual(response.context["repair_pending"], 1)

    @override_settings(
        STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
    )
    def test_management_dashboard_requires_management_access(self):
        user = get_user_model().objects.create_user(username="ceo", password="test-password")
        self.client.force_login(user)

        response = self.client.get(reverse("management_dashboard"))
        self.assertEqual(response.status_code, 403)

        user.groups.add(Group.objects.get(name="Management"))
        response = self.client.get(reverse("management_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Business Overview")

    def test_login_redirects_users_to_the_dashboard_matching_their_role(self):
        help_desk_user = get_user_model().objects.create_user(
            username="helpdesk", password="test-password"
        )
        management_user = get_user_model().objects.create_user(
            username="ceo", password="test-password"
        )
        management_user.groups.add(Group.objects.get(name="Management"))

        help_desk_login = self.client.post(reverse("login"), {
            "username": help_desk_user.username,
            "password": "test-password",
        })
        self.assertRedirects(help_desk_login, reverse("dashboard"), fetch_redirect_response=False)

        self.client.logout()
        management_login = self.client.post(reverse("login"), {
            "username": management_user.username,
            "password": "test-password",
        })
        self.assertRedirects(
            management_login,
            reverse("management_dashboard"),
            fetch_redirect_response=False,
        )

        self.client.logout()
        management_login_with_next = self.client.post(
            f"{reverse('login')}?next={reverse('repair_list')}",
            {"username": management_user.username, "password": "test-password"},
        )
        self.assertRedirects(
            management_login_with_next,
            reverse("management_dashboard"),
            fetch_redirect_response=False,
        )

    @override_settings(
        STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
    )
    def test_management_account_can_view_but_cannot_edit_tickets(self):
        user = get_user_model().objects.create_user(username="ceo", password="test-password")
        user.groups.add(Group.objects.get(name="Management"))
        self.client.force_login(user)

        response = self.client.get(reverse("repair_list"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("repair_create"))
        self.assertRedirects(response, reverse("management_dashboard"), fetch_redirect_response=False)

    def test_ajax_client_create_returns_json_on_success(self):
        user = get_user_model().objects.create_user(username="staff-ajax", password="test-password")
        self.client.force_login(user)
        response = self.client.post(
            reverse("client_create"),
            {"name": "New AJAX Client", "phone": "123456789"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["name"], "New AJAX Client")

    def test_ajax_client_create_returns_json_errors_on_invalid(self):
        user = get_user_model().objects.create_user(username="staff-ajax-err", password="test-password")
        self.client.force_login(user)
        response = self.client.post(
            reverse("client_create"),
            {"name": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("html", response.json())
        self.assertIn("This field is required", response.json()["html"])

    @override_settings(
        STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
    )
    def test_new_routes_return_ok_for_logged_in_staff(self):
        user = get_user_model().objects.create_user(username="staff-routes", password="test-password")
        self.client.force_login(user)
        
        # Test global search
        response = self.client.get(reverse("global_search"), {"q": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Results for \"test\"")
        
        # Test receipts
        job = RepairJob.objects.create(
            date_in=date.today(), client=self.client_a, received_by="Asha",
            machine=self.machine, problem_cause="Will not power on",
        )
        response = self.client.get(reverse("repair_receipt", args=[job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Intake Receipt")
        
        claim = WarrantyClaim.objects.create(
            date_in=date.today(), received_by="Asha", sold_to=self.client_a,
            machine=self.machine,
        )
        response = self.client.get(reverse("warranty_receipt", args=[claim.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Warranty Claim Slip")

    @override_settings(
        STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
    )
    def test_admin_monthly_and_client_filters(self):
        user = get_user_model().objects.create_user(username="admin_user", password="test-password")
        user.groups.add(Group.objects.get(name="Management"))
        self.client.force_login(user)

        # Create repair job for Asha in current month
        RepairJob.objects.create(
            date_in=date.today(), client=self.client_a, received_by="Staff",
            machine=self.machine, problem_cause="Screen broken",
        )

        # Monthly filter GET request
        curr_month = date.today().strftime("%Y-%m")
        response = self.client.get(reverse("management_dashboard"), {"month": curr_month})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["repairs_received_month"], 1)

        # Client filter GET request
        response = self.client.get(reverse("management_dashboard"), {"client_id": self.client_a.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_client"], self.client_a)

    @override_settings(
        STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
    )
    def test_client_list_and_client_detail_views(self):
        staff = get_user_model().objects.create_user(username="staff_member", password="test-password")
        self.client.force_login(staff)

        # Test client list view
        response = self.client.get(reverse("client_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Client Details")
        self.assertContains(response, self.client_a.name)

        # Test client detail view
        response = self.client.get(reverse("client_detail", args=[self.client_a.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.client_a.name)

    @override_settings(
        STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
    )
    def test_repair_and_warranty_list_client_filters(self):
        staff = get_user_model().objects.create_user(username="staff_filter", password="test-password")
        self.client.force_login(staff)

        job_a = RepairJob.objects.create(
            date_in=date.today(), client=self.client_a, received_by="Staff",
            machine=self.machine, problem_cause="Overheating",
        )

        # Filter repair list by client_a
        response = self.client.get(reverse("repair_list"), {"client_id": self.client_a.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn(job_a, response.context["jobs"])

        # Filter repair list by serial number
        response = self.client.get(reverse("repair_list"), {"serial_number": "SN-100"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(job_a, response.context["jobs"])

        # Filter repair list by date
        today_str = date.today().strftime("%Y-%m-%d")
        response = self.client.get(reverse("repair_list"), {"date_in": today_str})
        self.assertEqual(response.status_code, 200)
        self.assertIn(job_a, response.context["jobs"])

        # Filter warranty list by client_a
        claim_a = WarrantyClaim.objects.create(
            date_in=date.today(), received_by="Staff", sold_to=self.client_a,
            machine=self.machine,
        )
        response = self.client.get(reverse("warranty_list"), {"client_id": self.client_a.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn(claim_a, response.context["claims"])

    def test_nepali_date_conversion_and_tags(self):
        from datetime import date
        from service.nepali_date import ad_to_bs, bs_to_ad, ad_to_bs_display, bs_fiscal_year
        from service.templatetags.nepali_tags import to_bs, bs_fy

        # Base Reference test: AD 1943-04-14 should convert to BS 2000-01-01
        self.assertEqual(ad_to_bs(date(1943, 4, 14)), (2000, 1, 1))

        # Test reverse conversion: BS 2000-01-01 should convert back to AD 1943-04-14
        self.assertEqual(bs_to_ad(2000, 1, 1), date(1943, 4, 14))

        # Test display formats
        self.assertEqual(ad_to_bs_display(date(1943, 4, 14)), "Baisakh 1, 2000")
        self.assertEqual(to_bs(date(1943, 4, 14)), "Baisakh 1, 2000")

        # Test fiscal year
        self.assertEqual(bs_fiscal_year(date(2026, 8, 6)), "2083–84")
        self.assertEqual(bs_fy(date(2026, 8, 6)), "2083–84")

        # Test model properties
        job = RepairJob.objects.create(
            date_in=date(2026, 8, 6), client=self.client_a, received_by="Staff",
            machine=self.machine, problem_cause="Issue"
        )
        self.assertEqual(job.date_in_bs, "Shrawan 21, 2083")



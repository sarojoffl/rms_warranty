from django.urls import path

from . import views

urlpatterns = [
    path("", views.helpdesk_required(views.dashboard), name="dashboard"),
    path("management/", views.management_dashboard, name="management_dashboard"),
    path("management/logs/", views.management_logs, name="management_logs"),

    # Clients
    path("clients/", views.client_list, name="client_list"),
    path("clients/<int:pk>/", views.client_detail, name="client_detail"),
    path("clients/<int:pk>/edit/", views.client_edit, name="client_edit"),
    path("clients/new/", views.helpdesk_required(views.client_create), name="client_create"),
    path("machines/new/", views.helpdesk_required(views.machine_create), name="machine_create"),
    path("machines/<int:pk>/edit/", views.helpdesk_required(views.machine_edit), name="machine_edit"),
    path("machines/options/", views.helpdesk_required(views.machine_options), name="machine_options"),

    # RMS
    path("repair/", views.repair_list, name="repair_list"),
    path("repair/new/", views.helpdesk_required(views.repair_create), name="repair_create"),
    path("repair/<int:pk>/", views.repair_detail, name="repair_detail"),
    path("repair/<int:pk>/edit/", views.repair_edit, name="repair_edit"),
    path("repair/<int:pk>/exit/", views.helpdesk_required(views.repair_exit), name="repair_exit"),
    path("repair/<int:pk>/pdf/", views.repair_export_pdf, name="repair_export_pdf"),

    # Warranty
    path("warranty/", views.warranty_list, name="warranty_list"),
    path("warranty/new/", views.helpdesk_required(views.warranty_create), name="warranty_create"),
    path("warranty/<int:pk>/", views.warranty_detail, name="warranty_detail"),
    path("warranty/<int:pk>/edit/", views.warranty_edit, name="warranty_edit"),
    path("warranty/<int:pk>/exit/", views.helpdesk_required(views.warranty_exit), name="warranty_exit"),
    path("warranty/<int:pk>/pdf/client/", views.warranty_export_pdf_client, name="warranty_export_pdf_client"),
    path("warranty/<int:pk>/pdf/claim/", views.warranty_export_pdf_claim, name="warranty_export_pdf_claim"),
    
    # Universal Search
    path("search/", views.global_search, name="global_search"),
]

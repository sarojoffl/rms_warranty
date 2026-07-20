from django.urls import path

from . import views

urlpatterns = [
    path("", views.helpdesk_required(views.dashboard), name="dashboard"),
    path("management/", views.management_dashboard, name="management_dashboard"),
    path("management/logs/", views.management_logs, name="management_logs"),

    # Quick-create
    path("clients/new/", views.helpdesk_required(views.client_create), name="client_create"),
    path("machines/new/", views.helpdesk_required(views.machine_create), name="machine_create"),
    path("machines/options/", views.helpdesk_required(views.machine_options), name="machine_options"),

    # RMS
    path("repair/", views.repair_list, name="repair_list"),
    path("repair/new/", views.helpdesk_required(views.repair_create), name="repair_create"),
    path("repair/<int:pk>/", views.repair_detail, name="repair_detail"),
    path("repair/<int:pk>/exit/", views.helpdesk_required(views.repair_exit), name="repair_exit"),
    path("repair/<int:pk>/pdf/", views.repair_export_pdf, name="repair_export_pdf"),
    path("repair/<int:pk>/receipt/", views.repair_receipt, name="repair_receipt"),

    # Warranty
    path("warranty/", views.warranty_list, name="warranty_list"),
    path("warranty/new/", views.helpdesk_required(views.warranty_create), name="warranty_create"),
    path("warranty/<int:pk>/", views.warranty_detail, name="warranty_detail"),
    path("warranty/<int:pk>/exit/", views.helpdesk_required(views.warranty_exit), name="warranty_exit"),
    path("warranty/<int:pk>/pdf/", views.warranty_export_pdf, name="warranty_export_pdf"),
    path("warranty/<int:pk>/receipt/", views.warranty_receipt, name="warranty_receipt"),
    
    # Universal Search
    path("search/", views.global_search, name="global_search"),
]

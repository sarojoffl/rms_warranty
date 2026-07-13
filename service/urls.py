from django.urls import path

from . import views

urlpatterns = [
    # Quick-create
    path("clients/new/", views.client_create, name="client_create"),
    path("machines/new/", views.machine_create, name="machine_create"),

    # RMS
    path("repair/", views.repair_list, name="repair_list"),
    path("repair/new/", views.repair_create, name="repair_create"),
    path("repair/<int:pk>/", views.repair_detail, name="repair_detail"),
    path("repair/<int:pk>/exit/", views.repair_exit, name="repair_exit"),
    path("repair/<int:pk>/pdf/", views.repair_export_pdf, name="repair_export_pdf"),

    # Warranty
    path("warranty/", views.warranty_list, name="warranty_list"),
    path("warranty/new/", views.warranty_create, name="warranty_create"),
    path("warranty/<int:pk>/", views.warranty_detail, name="warranty_detail"),
    path("warranty/<int:pk>/exit/", views.warranty_exit, name="warranty_exit"),
    path("warranty/<int:pk>/pdf/", views.warranty_export_pdf, name="warranty_export_pdf"),
]

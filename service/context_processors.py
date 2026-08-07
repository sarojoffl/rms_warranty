from .views import is_management_user, is_repair_staff, is_warranty_staff


def role_context(request):
    return {
        "management_user": is_management_user(request.user),
        "repair_staff":    is_repair_staff(request.user),
        "warranty_staff":  is_warranty_staff(request.user),
    }

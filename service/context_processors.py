def role_context(request):
    return {
        "management_user": (
            request.user.is_authenticated
            and request.user.groups.filter(name="Management").exists()
        )
    }

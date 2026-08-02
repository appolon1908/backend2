from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnlyOrAdmin(BasePermission):
    """Allow public reads while limiting data mutations to Django staff."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

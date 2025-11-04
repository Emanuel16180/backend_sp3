from rest_framework.permissions import BasePermission


class IsClinicAdmin(BasePermission):
    """Permite acceso solo a usuarios autenticados cuyo user_type es 'admin'."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and getattr(request.user, 'user_type', None) == 'admin'
        )

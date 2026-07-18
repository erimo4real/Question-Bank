from django.contrib.auth.mixins import AccessMixin
from rest_framework import permissions


class AdminRequiredMixin(AccessMixin):
    """Deny access for non-admin users (admin + super_admin)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ("admin", "super_admin"):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(AccessMixin):
    """Deny access for non-super-admin users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != "super_admin":
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ("admin", "super_admin")


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "super_admin"


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "teacher"


class IsAdminOrTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ("admin", "super_admin", "teacher")

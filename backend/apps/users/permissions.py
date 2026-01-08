from rest_framework.permissions import BasePermission
from .models import UserRole


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.ADMIN)


class IsEmployer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "EMPLOYER")


class IsEmployerApproved(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.role == "EMPLOYER"):
            return False
        ep = getattr(request.user, "employer_profile", None)
        return bool(ep and getattr(ep, "status", None) == "APPROVED")


class IsCandidate(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "CANDIDATE")

"""Test-only URLconf exposing role-protected and object-protected demo endpoints."""

from django.urls import include, path
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    IsAdministrator,
    IsEmployer,
    IsInstructor,
    IsModerator,
    IsObjectOwner,
    IsStudent,
)
from apps.companies.models import Company


def role_view(permission):
    class RoleView(APIView):
        permission_classes = [permission]

        def get(self, request):
            return Response({"ok": True})

    return RoleView.as_view()


class CompanyDetailView(APIView):
    """Models a future per-object resource: employers may only read their own company."""

    permission_classes = [IsAuthenticated, IsEmployer, IsObjectOwner]
    owner_field = "owner"

    def get(self, request, pk):
        from rest_framework.generics import get_object_or_404

        company = get_object_or_404(Company, pk=pk)
        self.check_object_permissions(request, company)
        return Response({"name": company.name})


urlpatterns = [
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("t/student/", role_view(IsStudent)),
    path("t/employer/", role_view(IsEmployer)),
    path("t/instructor/", role_view(IsInstructor)),
    path("t/moderator/", role_view(IsModerator)),
    path("t/admin/", role_view(IsAdministrator)),
    path("t/company/<uuid:pk>/", CompanyDetailView.as_view()),
]

"""Reusable server-side authorization. Use these instead of comparing role strings in views."""

from rest_framework.permissions import BasePermission

from .models import UserRole


class HasRole(BasePermission):
    """Allow authenticated, active users whose database role is in `allowed_roles`."""

    allowed_roles: frozenset[str] = frozenset()

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.can_authenticate
            and user.role in self.allowed_roles
        )


class IsStudent(HasRole):
    allowed_roles = frozenset({UserRole.STUDENT})


class IsEmployer(HasRole):
    allowed_roles = frozenset({UserRole.EMPLOYER})


class IsInstructor(HasRole):
    allowed_roles = frozenset({UserRole.INSTRUCTOR})


class IsModerator(HasRole):
    allowed_roles = frozenset({UserRole.MODERATOR})


class IsAdministrator(HasRole):
    allowed_roles = frozenset({UserRole.ADMINISTRATOR})


class IsObjectOwner(BasePermission):
    """Object-level check: the object's owner must be the requesting user.

    Views set `owner_field` (default "owner"; may traverse relations with "__",
    e.g. "company__owner"). Pair with a role permission and a queryset that is
    already scoped to the user, so IDs from the client never grant access.
    """

    def has_object_permission(self, request, view, obj):
        path = getattr(view, "owner_field", "owner")
        owner = obj
        for part in path.split("__"):
            owner = getattr(owner, part, None)
        return owner is not None and owner == request.user

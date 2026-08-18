from rest_framework.permissions import BasePermission

from .models import OrganizationMembership


class IsOrganizationMember(BasePermission):
    message = "You must belong to this organization."

    def has_object_permission(self, request, view, organization):
        if not request.user.is_authenticated:
            return False
        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
        ).exists()


class IsOrganizationAdmin(BasePermission):
    message = "Only organization owners and admins can perform this action."

    def has_object_permission(self, request, view, organization):
        if not request.user.is_authenticated:
            return False
        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            role__in=[
                OrganizationMembership.Role.OWNER,
                OrganizationMembership.Role.ADMIN,
            ],
        ).exists()


class IsOrganizationOwner(BasePermission):
    message = "Only the organization owner can perform this action."

    def has_object_permission(self, request, view, organization):
        if not request.user.is_authenticated:
            return False
        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            role=OrganizationMembership.Role.OWNER,
        ).exists()

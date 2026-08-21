from rest_framework.permissions import BasePermission

from apps.organizations.models import OrganizationMembership


class IsCompetitionManager(BasePermission):
    message = "Only organization owners and admins can manage competition data."

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

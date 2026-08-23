from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import response_for_queryset
from apps.common.query_params import apply_query_options

from .models import Organization, OrganizationMembership
from .permissions import (
    IsOrganizationAdmin,
    IsOrganizationMember,
    IsOrganizationOwner,
)
from .serializers import (
    MembershipCreateSerializer,
    MembershipRoleSerializer,
    MembershipSerializer,
    OrganizationSerializer,
)

User = get_user_model()


class OrganizationScopedMixin:
    def get_organization_queryset(self, request):
        return Organization.objects.filter(
            memberships__user=request.user,
        ).annotate(current_user_role=F("memberships__role"))

    def get_organization(self, request, organization_id):
        organization = get_object_or_404(
            self.get_organization_queryset(request),
            pk=organization_id,
        )
        self.check_object_permissions(request, organization)
        return organization

    def require_admin(self, request, organization):
        if not IsOrganizationAdmin().has_object_permission(
            request,
            self,
            organization,
        ):
            raise PermissionDenied(IsOrganizationAdmin.message)

    def require_owner(self, request, organization):
        if not IsOrganizationOwner().has_object_permission(
            request,
            self,
            organization,
        ):
            raise PermissionDenied(IsOrganizationOwner.message)


class OrganizationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OrganizationSerializer(many=True))
    def get(self, request):
        organizations = Organization.objects.filter(
            memberships__user=request.user,
        ).annotate(current_user_role=F("memberships__role"))
        organizations = apply_query_options(
            organizations,
            request,
            search_fields=("name", "slug"),
            ordering_fields=("name", "slug", "created_at"),
            default_ordering=("name", "id"),
        )
        return response_for_queryset(
            organizations,
            request,
            OrganizationSerializer,
            view=self,
        )

    @extend_schema(
        request=OrganizationSerializer,
        responses={201: OrganizationSerializer},
    )
    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            organization = serializer.save(created_by=request.user)
            OrganizationMembership.objects.create(
                organization=organization,
                user=request.user,
                role=OrganizationMembership.Role.OWNER,
            )

        organization = Organization.objects.annotate(
            current_user_role=F("memberships__role")
        ).get(pk=organization.pk)
        return Response(
            OrganizationSerializer(organization).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationDetailView(OrganizationScopedMixin, APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @extend_schema(responses=OrganizationSerializer)
    def get(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        return Response(OrganizationSerializer(organization).data)

    @extend_schema(
        request=OrganizationSerializer,
        responses=OrganizationSerializer,
    )
    def patch(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        self.require_admin(request, organization)
        serializer = OrganizationSerializer(
            organization,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        return Response(OrganizationSerializer(organization).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        self.require_owner(request, organization)
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MembershipListCreateView(OrganizationScopedMixin, APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @extend_schema(responses=MembershipSerializer(many=True))
    def get(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        memberships = organization.memberships.select_related("user").all()
        memberships = apply_query_options(
            memberships,
            request,
            search_fields=("user__email", "role"),
            ordering_fields=("role", "created_at"),
            default_ordering=("user__email", "id"),
        )
        return response_for_queryset(
            memberships,
            request,
            MembershipSerializer,
            view=self,
        )

    @extend_schema(
        request=MembershipCreateSerializer,
        responses={201: MembershipSerializer},
    )
    def post(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        self.require_admin(request, organization)
        serializer = MembershipCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email__iexact=serializer.validated_data["email"])
        try:
            membership = OrganizationMembership.objects.create(
                organization=organization,
                user=user,
                role=serializer.validated_data["role"],
            )
        except IntegrityError as exc:
            raise ValidationError(
                {"email": "This user already belongs to the organization."}
            ) from exc
        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )


class MembershipDetailView(OrganizationScopedMixin, APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_membership(self, request, organization_id, membership_id):
        organization = self.get_organization(request, organization_id)
        membership = get_object_or_404(
            organization.memberships.select_related("user"),
            pk=membership_id,
        )
        return organization, membership

    @extend_schema(responses=MembershipSerializer)
    def get(self, request, organization_id, membership_id):
        _, membership = self.get_membership(request, organization_id, membership_id)
        return Response(MembershipSerializer(membership).data)

    @extend_schema(
        request=MembershipRoleSerializer,
        responses=MembershipSerializer,
    )
    def patch(self, request, organization_id, membership_id):
        organization, membership = self.get_membership(
            request,
            organization_id,
            membership_id,
        )
        self.require_admin(request, organization)
        if membership.role == OrganizationMembership.Role.OWNER:
            raise PermissionDenied("The owner membership cannot be changed.")
        serializer = MembershipRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership.role = serializer.validated_data["role"]
        membership.save(update_fields=["role", "updated_at"])
        return Response(MembershipSerializer(membership).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, organization_id, membership_id):
        organization, membership = self.get_membership(
            request,
            organization_id,
            membership_id,
        )
        self.require_admin(request, organization)
        if membership.role == OrganizationMembership.Role.OWNER:
            raise PermissionDenied("The owner membership cannot be removed.")
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

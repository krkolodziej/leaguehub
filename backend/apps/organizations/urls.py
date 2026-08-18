from django.urls import path

from .views import (
    MembershipDetailView,
    MembershipListCreateView,
    OrganizationDetailView,
    OrganizationListCreateView,
)

urlpatterns = [
    path(
        "organizations/",
        OrganizationListCreateView.as_view(),
        name="organization-list-create",
    ),
    path(
        "organizations/<int:organization_id>/",
        OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
    path(
        "organizations/<int:organization_id>/members/",
        MembershipListCreateView.as_view(),
        name="membership-list-create",
    ),
    path(
        "organizations/<int:organization_id>/members/<int:membership_id>/",
        MembershipDetailView.as_view(),
        name="membership-detail",
    ),
]

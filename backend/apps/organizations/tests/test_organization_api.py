import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import OrganizationMembership


def make_user(email):
    return User.objects.create_user(email, password="StrongPassword123!")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_organization(client, name="Python League", slug="python-league"):
    response = client.post(
        "/api/v1/organizations/",
        {"name": name, "slug": slug},
        format="json",
    )
    assert response.status_code == 201
    return response.data


@pytest.mark.django_db
def test_create_organization_creates_owner_membership():
    owner = make_user("owner@example.com")
    response = create_organization(client_for(owner))

    membership = OrganizationMembership.objects.get(
        organization_id=response["id"],
        user=owner,
    )

    assert response["my_role"] == OrganizationMembership.Role.OWNER
    assert response["created_by_id"] == owner.id
    assert membership.role == OrganizationMembership.Role.OWNER


@pytest.mark.django_db
def test_user_can_list_only_organizations_they_belong_to():
    owner_a = make_user("owner-a@example.com")
    owner_b = make_user("owner-b@example.com")
    create_organization(client_for(owner_a), slug="organization-a")
    organization_b = create_organization(
        client_for(owner_b),
        name="Organization B",
        slug="organization-b",
    )

    response = client_for(owner_a).get("/api/v1/organizations/")
    cross_tenant_detail = client_for(owner_a).get(
        f"/api/v1/organizations/{organization_b['id']}/"
    )
    cross_tenant_members = client_for(owner_a).get(
        f"/api/v1/organizations/{organization_b['id']}/members/"
    )

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["slug"] == "organization-a"
    assert cross_tenant_detail.status_code == 404
    assert cross_tenant_members.status_code == 404


@pytest.mark.django_db
def test_member_can_read_but_cannot_manage_organization():
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization = create_organization(client_for(owner))
    OrganizationMembership.objects.create(
        organization_id=organization["id"],
        user=member,
        role=OrganizationMembership.Role.MEMBER,
    )

    client = client_for(member)
    detail = client.get(f"/api/v1/organizations/{organization['id']}/")
    update = client.patch(
        f"/api/v1/organizations/{organization['id']}/",
        {"name": "Should not change"},
        format="json",
    )
    add_member = client.post(
        f"/api/v1/organizations/{organization['id']}/members/",
        {"email": "new@example.com", "role": "MEMBER"},
        format="json",
    )

    assert detail.status_code == 200
    assert update.status_code == 403
    assert add_member.status_code == 403


@pytest.mark.django_db
def test_owner_can_add_member_and_duplicate_membership_is_rejected():
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization = create_organization(client_for(owner))
    url = f"/api/v1/organizations/{organization['id']}/members/"

    created = client_for(owner).post(
        url,
        {"email": " MEMBER@example.com ", "role": "MEMBER"},
        format="json",
    )
    duplicate = client_for(owner).post(
        url,
        {"email": member.email, "role": "MEMBER"},
        format="json",
    )

    assert created.status_code == 201
    assert created.data["email"] == member.email
    assert created.data["role"] == OrganizationMembership.Role.MEMBER
    assert duplicate.status_code == 400


@pytest.mark.django_db
def test_admin_can_change_and_remove_non_owner_members():
    owner = make_user("owner@example.com")
    admin = make_user("admin@example.com")
    member = make_user("member@example.com")
    organization = create_organization(client_for(owner))
    organization_id = organization["id"]
    OrganizationMembership.objects.create(
        organization_id=organization_id,
        user=admin,
        role=OrganizationMembership.Role.ADMIN,
    )
    member_membership = OrganizationMembership.objects.create(
        organization_id=organization_id,
        user=member,
        role=OrganizationMembership.Role.MEMBER,
    )

    member_url = (
        f"/api/v1/organizations/{organization_id}/members/"
        f"{member_membership.id}/"
    )
    changed = client_for(admin).patch(
        member_url,
        {"role": "ADMIN"},
        format="json",
    )
    removed = client_for(admin).delete(member_url)

    assert changed.status_code == 200
    assert changed.data["role"] == OrganizationMembership.Role.ADMIN
    assert removed.status_code == 204
    assert not OrganizationMembership.objects.filter(pk=member_membership.id).exists()


@pytest.mark.django_db
def test_owner_membership_cannot_be_changed_or_removed():
    owner = make_user("owner@example.com")
    organization = create_organization(client_for(owner))
    owner_membership = OrganizationMembership.objects.get(
        organization_id=organization["id"],
        user=owner,
    )
    url = (
        f"/api/v1/organizations/{organization['id']}/members/"
        f"{owner_membership.id}/"
    )

    changed = client_for(owner).patch(url, {"role": "MEMBER"}, format="json")
    removed = client_for(owner).delete(url)

    assert changed.status_code == 403
    assert removed.status_code == 403

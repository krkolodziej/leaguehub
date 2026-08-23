import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.competitions.models import League, Season, Team
from apps.organizations.models import Organization, OrganizationMembership


def make_owner(email="hardening-owner@example.com"):
    user = User.objects.create_user(email, password="StrongPassword123!")
    organization = Organization.objects.create(
        name="Hardening Org",
        slug="hardening-org",
        created_by=user,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.OWNER,
    )
    return user, organization


@pytest.mark.django_db
def test_unauthenticated_api_returns_401_with_consistent_code():
    response = APIClient().get("/api/v1/organizations/")

    assert response.status_code == 401
    assert response.data["code"] == "authentication_required"


@pytest.mark.django_db
def test_collection_supports_search_ordering_and_optional_pagination():
    owner, organization = make_owner()
    Team.objects.create(organization=organization, name="Alpha", slug="alpha")
    Team.objects.create(organization=organization, name="Bravo", slug="bravo")
    Team.objects.create(organization=organization, name="Alpine", slug="alpine")
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get(
        f"/api/v1/organizations/{organization.id}/teams/?search=al&ordering=-name"
        "&page=1&page_size=1"
    )

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Alpine"
    assert response.data["next"] is not None


@pytest.mark.django_db
def test_invalid_ordering_has_consistent_validation_error():
    owner, organization = make_owner("ordering-owner@example.com")
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get(
        f"/api/v1/organizations/{organization.id}/teams/?ordering=secret_field"
    )

    assert response.status_code == 400
    assert response.data["code"] == "validation_error"
    assert response.data["detail"] == "Request validation failed."
    assert "ordering" in response.data["fields"]


@pytest.mark.django_db
def test_permission_and_not_found_errors_have_stable_codes():
    owner, organization = make_owner("permission-owner@example.com")
    member = User.objects.create_user(
        "permission-member@example.com", password="StrongPassword123!"
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=member,
        role=OrganizationMembership.Role.MEMBER,
    )
    member_client = APIClient()
    member_client.force_authenticate(user=member)
    forbidden = member_client.post(
        f"/api/v1/organizations/{organization.id}/teams/",
        {"name": "Blocked", "slug": "blocked"},
        format="json",
    )
    missing = member_client.get("/api/v1/organizations/999999/teams/")

    assert forbidden.status_code == 403
    assert forbidden.data["code"] == "permission_denied"
    assert missing.status_code == 404
    assert missing.data["code"] == "not_found"


@pytest.mark.django_db
def test_fixture_conflict_has_consistent_conflict_code():
    owner, organization = make_owner("conflict-owner@example.com")
    league = League.objects.create(
        organization=organization,
        name="Conflict League",
        slug="conflict-league",
    )
    season = Season.objects.create(
        league=league,
        name="2026",
        start_date="2026-09-01",
    )
    teams = [
        Team.objects.create(
            organization=organization,
            name=f"Team {index}",
            slug=f"conflict-team-{index}",
        )
        for index in range(2)
    ]
    from apps.competitions.models import SeasonTeam

    SeasonTeam.objects.bulk_create(
        [SeasonTeam(season=season, team=team) for team in teams]
    )
    client = APIClient()
    client.force_authenticate(user=owner)
    url = (
        f"/api/v1/organizations/{organization.id}/leagues/{league.id}"
        f"/seasons/{season.id}/fixtures/"
    )
    assert client.post(url, {}, format="json").status_code == 201
    conflict = client.post(url, {}, format="json")

    assert conflict.status_code == 409
    assert conflict.data["code"] == "conflict"

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.competitions.models import Fixture, League, Season, SeasonTeam, Team
from apps.competitions.services.fixture_generator import (
    RoundRobinFixtureGenerator,
)
from apps.organizations.models import Organization, OrganizationMembership


def make_user(email):
    return User.objects.create_user(email, password="StrongPassword123!")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_season(team_count=4):
    owner = make_user(f"owner-{team_count}@example.com")
    organization = Organization.objects.create(
        name=f"Organization {team_count}",
        slug=f"organization-{team_count}",
        created_by=owner,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=owner,
        role=OrganizationMembership.Role.OWNER,
    )
    league = League.objects.create(
        organization=organization,
        name="Premier Python",
        slug=f"premier-python-{team_count}",
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
            slug=f"team-{team_count}-{index}",
        )
        for index in range(team_count)
    ]
    SeasonTeam.objects.bulk_create(
        [SeasonTeam(season=season, team=team) for team in teams]
    )
    return owner, organization, league, season, teams


@pytest.mark.django_db
def test_fixture_api_generates_single_round_robin_and_is_idempotent():
    owner, organization, league, season, _ = make_season()
    url = (
        f"/api/v1/organizations/{organization.id}/leagues/{league.id}"
        f"/seasons/{season.id}/fixtures/"
    )
    client = client_for(owner)

    generated = client.post(url, {"double_round_robin": False}, format="json")
    repeated = client.post(url, {"double_round_robin": False}, format="json")
    listed = client.get(url)

    assert generated.status_code == 201
    assert len(generated.data) == 6
    assert repeated.status_code == 409
    assert listed.status_code == 200
    assert len(listed.data) == 6
    assert Fixture.objects.filter(season=season).count() == 6


@pytest.mark.django_db
def test_fixture_api_generates_double_round_robin():
    owner, organization, league, season, _ = make_season()
    url = (
        f"/api/v1/organizations/{organization.id}/leagues/{league.id}"
        f"/seasons/{season.id}/fixtures/"
    )

    response = client_for(owner).post(
        url,
        {"double_round_robin": True},
        format="json",
    )
    fixtures = Fixture.objects.filter(season=season)
    directions = {(fixture.home_team_id, fixture.away_team_id) for fixture in fixtures}

    assert response.status_code == 201
    assert fixtures.count() == 12
    assert len(directions) == 12


@pytest.mark.django_db
def test_fixture_generation_requires_two_season_teams():
    owner, organization, league, season, _ = make_season(team_count=1)
    url = (
        f"/api/v1/organizations/{organization.id}/leagues/{league.id}"
        f"/seasons/{season.id}/fixtures/"
    )

    response = client_for(owner).post(url, {}, format="json")

    assert response.status_code == 400
    assert Fixture.objects.filter(season=season).count() == 0


@pytest.mark.django_db
def test_member_cannot_generate_fixtures():
    owner, organization, league, season, _ = make_season()
    member = make_user("member-fixtures@example.com")
    OrganizationMembership.objects.create(
        organization=organization,
        user=member,
        role=OrganizationMembership.Role.MEMBER,
    )
    url = (
        f"/api/v1/organizations/{organization.id}/leagues/{league.id}"
        f"/seasons/{season.id}/fixtures/"
    )

    response = client_for(member).post(url, {}, format="json")

    assert response.status_code == 403
    assert Fixture.objects.filter(season=season).count() == 0


@pytest.mark.django_db
def test_service_persists_fixture_schedule_atomically():
    _, _, _, season, _ = make_season()

    fixtures = RoundRobinFixtureGenerator.generate_for_season(
        season,
        double_round_robin=False,
    )

    assert len(fixtures) == 6
    assert Fixture.objects.filter(season=season).count() == 6

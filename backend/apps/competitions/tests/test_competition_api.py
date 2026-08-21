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


def create_organization(client, name="Python League Org", slug="python-league-org"):
    response = client.post(
        "/api/v1/organizations/",
        {"name": name, "slug": slug},
        format="json",
    )
    assert response.status_code == 201
    return response.data


def create_domain(client, organization_id):
    root = f"/api/v1/organizations/{organization_id}"
    league = client.post(
        f"{root}/leagues/",
        {"name": "Premier Python", "slug": "premier-python"},
        format="json",
    )
    season = client.post(
        f"{root}/leagues/{league.data['id']}/seasons/",
        {
            "name": "2026",
            "start_date": "2026-09-01",
            "end_date": "2027-05-31",
        },
        format="json",
    )
    team = client.post(
        f"{root}/teams/",
        {"name": "Django United", "slug": "django-united"},
        format="json",
    )
    player = client.post(
        f"{root}/players/",
        {"first_name": "Ada", "last_name": "Lovelace"},
        format="json",
    )
    assert league.status_code == 201
    assert season.status_code == 201
    assert team.status_code == 201
    assert player.status_code == 201
    return league.data, season.data, team.data, player.data


def season_team_url(organization_id, league_id, season_id):
    return (
        f"/api/v1/organizations/{organization_id}/leagues/{league_id}"
        f"/seasons/{season_id}/teams/"
    )


@pytest.mark.django_db
def test_create_domain_and_roster_entry():
    owner = make_user("owner@example.com")
    organization = create_organization(client_for(owner))
    client = client_for(owner)
    league, season, team, player = create_domain(client, organization["id"])

    season_teams = season_team_url(
        organization["id"],
        league["id"],
        season["id"],
    )
    season_team = client.post(
        season_teams,
        {"team_id": team["id"]},
        format="json",
    )
    roster_url = f"{season_teams}{season_team.data['id']}/roster/"
    roster_entry = client.post(
        roster_url,
        {
            "player_id": player["id"],
            "shirt_number": 10,
            "position": "Midfielder",
            "is_captain": True,
        },
        format="json",
    )

    assert season_team.status_code == 201
    assert season_team.data["team_id"] == team["id"]
    assert season_team.data["team_name"] == "Django United"
    assert roster_entry.status_code == 201
    assert roster_entry.data["player_name"] == "Ada Lovelace"
    assert roster_entry.data["shirt_number"] == 10


@pytest.mark.django_db
def test_season_team_and_roster_constraints_reject_duplicates():
    owner = make_user("owner@example.com")
    organization = create_organization(client_for(owner))
    client = client_for(owner)
    league, season, team, player = create_domain(client, organization["id"])
    season_teams = season_team_url(
        organization["id"],
        league["id"],
        season["id"],
    )
    first_season_team = client.post(
        season_teams,
        {"team_id": team["id"]},
        format="json",
    )
    duplicate_season_team = client.post(
        season_teams,
        {"team_id": team["id"]},
        format="json",
    )
    roster_url = f"{season_teams}{first_season_team.data['id']}/roster/"
    first_entry = client.post(
        roster_url,
        {"player_id": player["id"], "shirt_number": 10},
        format="json",
    )
    duplicate_player = client.post(
        roster_url,
        {"player_id": player["id"], "shirt_number": 11},
        format="json",
    )

    assert first_season_team.status_code == 201
    assert duplicate_season_team.status_code == 400
    assert first_entry.status_code == 201
    assert duplicate_player.status_code == 400


@pytest.mark.django_db
def test_roster_rejects_duplicate_shirt_number_and_captain():
    owner = make_user("owner@example.com")
    organization = create_organization(client_for(owner))
    client = client_for(owner)
    league, season, team, player = create_domain(client, organization["id"])
    second_player = client.post(
        f"/api/v1/organizations/{organization['id']}/players/",
        {"first_name": "Grace", "last_name": "Hopper"},
        format="json",
    )
    season_teams = season_team_url(
        organization["id"],
        league["id"],
        season["id"],
    )
    season_team = client.post(
        season_teams,
        {"team_id": team["id"]},
        format="json",
    )
    roster_url = f"{season_teams}{season_team.data['id']}/roster/"
    first_entry = client.post(
        roster_url,
        {
            "player_id": player["id"],
            "shirt_number": 10,
            "is_captain": True,
        },
        format="json",
    )
    duplicate_shirt = client.post(
        roster_url,
        {"player_id": second_player.data["id"], "shirt_number": 10},
        format="json",
    )
    duplicate_captain = client.post(
        roster_url,
        {
            "player_id": second_player.data["id"],
            "shirt_number": 11,
            "is_captain": True,
        },
        format="json",
    )

    assert first_entry.status_code == 201
    assert duplicate_shirt.status_code == 400
    assert duplicate_captain.status_code == 400


@pytest.mark.django_db
def test_player_can_be_rostered_for_multiple_season_teams():
    owner = make_user("owner@example.com")
    organization = create_organization(client_for(owner))
    client = client_for(owner)
    league, season, team, player = create_domain(client, organization["id"])
    second_team = client.post(
        f"/api/v1/organizations/{organization['id']}/teams/",
        {"name": "React Rovers", "slug": "react-rovers"},
        format="json",
    )
    season_teams = season_team_url(
        organization["id"],
        league["id"],
        season["id"],
    )
    first_season_team = client.post(
        season_teams,
        {"team_id": team["id"]},
        format="json",
    )
    second_season_team = client.post(
        season_teams,
        {"team_id": second_team.data["id"]},
        format="json",
    )
    first_roster = client.post(
        f"{season_teams}{first_season_team.data['id']}/roster/",
        {"player_id": player["id"], "shirt_number": 10},
        format="json",
    )
    second_roster = client.post(
        f"{season_teams}{second_season_team.data['id']}/roster/",
        {"player_id": player["id"], "shirt_number": 7},
        format="json",
    )

    assert first_roster.status_code == 201
    assert second_roster.status_code == 201


@pytest.mark.django_db
def test_cross_organization_team_cannot_be_added_to_season():
    owner_a = make_user("owner-a@example.com")
    owner_b = make_user("owner-b@example.com")
    organization_a = create_organization(
        client_for(owner_a),
        name="Organization A",
        slug="organization-a",
    )
    organization_b = create_organization(
        client_for(owner_b),
        name="Organization B",
        slug="organization-b",
    )
    league, season, _, _ = create_domain(
        client_for(owner_a),
        organization_a["id"],
    )
    team_b = client_for(owner_b).post(
        f"/api/v1/organizations/{organization_b['id']}/teams/",
        {"name": "Other Team", "slug": "other-team"},
        format="json",
    )

    response = client_for(owner_a).post(
        season_team_url(
            organization_a["id"],
            league["id"],
            season["id"],
        ),
        {"team_id": team_b.data["id"]},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_member_can_read_domain_but_cannot_manage_it():
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization = create_organization(client_for(owner))
    OrganizationMembership.objects.create(
        organization_id=organization["id"],
        user=member,
        role=OrganizationMembership.Role.MEMBER,
    )
    league, _, _, _ = create_domain(client_for(owner), organization["id"])
    member_client = client_for(member)
    root = f"/api/v1/organizations/{organization['id']}"

    read_response = member_client.get(f"{root}/leagues/")
    write_response = member_client.post(
        f"{root}/leagues/",
        {"name": "Forbidden League", "slug": "forbidden-league"},
        format="json",
    )
    detail_response = member_client.get(f"{root}/leagues/{league['id']}/")

    assert read_response.status_code == 200
    assert write_response.status_code == 403
    assert detail_response.status_code == 200


@pytest.mark.django_db
def test_cross_tenant_domain_is_not_visible():
    owner_a = make_user("owner-a@example.com")
    owner_b = make_user("owner-b@example.com")
    organization_a = create_organization(
        client_for(owner_a),
        name="Organization A",
        slug="organization-a",
    )
    organization_b = create_organization(
        client_for(owner_b),
        name="Organization B",
        slug="organization-b",
    )
    league_b, _, _, _ = create_domain(
        client_for(owner_b),
        organization_b["id"],
    )

    response = client_for(owner_a).get(
        f"/api/v1/organizations/{organization_b['id']}/leagues/"
    )
    detail = client_for(owner_a).get(
        f"/api/v1/organizations/{organization_b['id']}/leagues/{league_b['id']}/"
    )
    own_organizations = client_for(owner_a).get(
        "/api/v1/organizations/"
    )

    assert response.status_code == 404
    assert detail.status_code == 404
    assert own_organizations.status_code == 200
    assert own_organizations.data[0]["id"] == organization_a["id"]

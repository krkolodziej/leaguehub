import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.competitions.models import (
    Fixture,
    League,
    Player,
    RosterEntry,
    Season,
    SeasonTeam,
    Team,
)
from apps.organizations.models import Organization, OrganizationMembership

from apps.matches.models import Match, MatchEvent


def make_user(email):
    return User.objects.create_user(email, password="StrongPassword123!")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_match_data():
    owner = make_user("match-owner@example.com")
    member = make_user("match-member@example.com")
    organization = Organization.objects.create(
        name="Match Org", slug="match-org", created_by=owner
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=owner,
        role=OrganizationMembership.Role.OWNER,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=member,
        role=OrganizationMembership.Role.MEMBER,
    )
    league = League.objects.create(
        organization=organization, name="League", slug="match-league"
    )
    season = Season.objects.create(
        league=league, name="2026", start_date="2026-09-01"
    )
    home_team = Team.objects.create(
        organization=organization, name="Home", slug="home"
    )
    away_team = Team.objects.create(
        organization=organization, name="Away", slug="away"
    )
    home_season_team = SeasonTeam.objects.create(season=season, team=home_team)
    away_season_team = SeasonTeam.objects.create(season=season, team=away_team)
    home_player = Player.objects.create(
        organization=organization, first_name="Home", last_name="Player"
    )
    away_player = Player.objects.create(
        organization=organization, first_name="Away", last_name="Player"
    )
    RosterEntry.objects.create(season_team=home_season_team, player=home_player)
    RosterEntry.objects.create(season_team=away_season_team, player=away_player)
    fixture = Fixture.objects.create(
        season=season,
        home_team=home_team,
        away_team=away_team,
        round_number=1,
        leg=1,
    )
    return owner, member, organization, league, season, fixture, home_team, home_player


def match_url(organization, league, season, suffix=""):
    return (
        f"/api/v1/organizations/{organization.id}/leagues/{league.id}"
        f"/seasons/{season.id}/matches/{suffix}"
    )


@pytest.mark.django_db
def test_match_lifecycle_and_goal_updates_score_atomically():
    owner, _, organization, league, season, fixture, home_team, home_player = make_match_data()
    client = client_for(owner)
    collection_url = match_url(organization, league, season)

    created = client.post(collection_url, {"fixture_id": fixture.id}, format="json")
    assert created.status_code == 201
    match = Match.objects.get(fixture=fixture)
    match_id = match.id

    started = client.post(match_url(organization, league, season, f"{match_id}/start/"))
    assert started.status_code == 200
    assert started.data["status"] == Match.Status.LIVE

    event_url = match_url(organization, league, season, f"{match_id}/events/")
    goal = client.post(
        event_url,
        {
            "event_type": "GOAL",
            "minute": 12,
            "team_id": home_team.id,
            "player_id": home_player.id,
        },
        format="json",
    )
    assert goal.status_code == 201
    match.refresh_from_db()
    assert match.home_score == 1
    assert MatchEvent.objects.filter(match=match).count() == 1

    finished = client.post(match_url(organization, league, season, f"{match_id}/finish/"))
    assert finished.status_code == 200
    assert finished.data["status"] == Match.Status.FINISHED

    after_finish = client.post(
        event_url,
        {
            "event_type": "GOAL",
            "minute": 90,
            "team_id": home_team.id,
            "player_id": home_player.id,
        },
        format="json",
    )
    assert after_finish.status_code == 400
    match.refresh_from_db()
    assert match.home_score == 1
    assert MatchEvent.objects.filter(match=match).count() == 1


@pytest.mark.django_db
def test_match_permissions_and_duplicate_fixture_match():
    owner, member, organization, league, season, fixture, *_ = make_match_data()
    owner_client = client_for(owner)
    member_client = client_for(member)
    url = match_url(organization, league, season)

    assert owner_client.post(url, {"fixture_id": fixture.id}, format="json").status_code == 201
    duplicate = owner_client.post(url, {"fixture_id": fixture.id}, format="json")
    assert duplicate.status_code == 409

    match_id = Match.objects.get(fixture=fixture).id
    start_url = match_url(organization, league, season, f"{match_id}/start/")
    assert member_client.post(start_url).status_code == 403
    assert member_client.get(url).status_code == 200


@pytest.mark.django_db
def test_invalid_goal_does_not_change_score_or_create_event():
    owner, _, organization, league, season, fixture, home_team, home_player = make_match_data()
    client = client_for(owner)
    client.post(match_url(organization, league, season), {"fixture_id": fixture.id}, format="json")
    match = Match.objects.get(fixture=fixture)
    client.post(match_url(organization, league, season, f"{match.id}/start/"))
    foreign_player = Player.objects.create(
        organization=fixture.season.league.organization,
        first_name="Unrostered",
        last_name="Player",
    )
    response = client.post(
        match_url(organization, league, season, f"{match.id}/events/"),
        {
            "event_type": "GOAL",
            "minute": 10,
            "team_id": home_team.id,
            "player_id": foreign_player.id,
        },
        format="json",
    )
    assert response.status_code == 400
    match.refresh_from_db()
    assert match.home_score == 0
    assert MatchEvent.objects.filter(match=match).count() == 0

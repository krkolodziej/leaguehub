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
from apps.competitions.services.player_statistics import get_season_player_statistics
from apps.competitions.services.standings import get_season_standings
from apps.matches.models import Match, MatchEvent
from apps.organizations.models import Organization, OrganizationMembership


def make_data():
    owner = User.objects.create_user("standings-owner@example.com", password="StrongPassword123!")
    member = User.objects.create_user("standings-member@example.com", password="StrongPassword123!")
    organization = Organization.objects.create(
        name="Standings Org", slug="standings-org", created_by=owner
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
        organization=organization, name="Standings League", slug="standings-league"
    )
    season = Season.objects.create(
        league=league, name="2026", start_date="2026-09-01"
    )
    teams = [
        Team.objects.create(
            organization=organization,
            name=name,
            slug=name.lower(),
        )
        for name in ["Alpha", "Bravo", "Charlie"]
    ]
    season_teams = [
        SeasonTeam.objects.create(season=season, team=team) for team in teams
    ]
    players = []
    for index, season_team in enumerate(season_teams):
        player = Player.objects.create(
            organization=organization,
            first_name=f"Player{index}",
            last_name=f"{teams[index].name}",
        )
        RosterEntry.objects.create(season_team=season_team, player=player)
        players.append(player)
    return owner, member, organization, league, season, teams, players


def make_finished_match(season, home_team, away_team, home_score, away_score):
    fixture = Fixture.objects.create(
        season=season,
        home_team=home_team,
        away_team=away_team,
        round_number=1,
    )
    return Match.objects.create(
        fixture=fixture,
        status=Match.Status.FINISHED,
        home_score=home_score,
        away_score=away_score,
    )


def season_url(organization, league, season, suffix):
    return (
        f"/api/v1/organizations/{organization.id}/leagues/{league.id}"
        f"/seasons/{season.id}/{suffix}"
    )


@pytest.mark.django_db
def test_standings_use_finished_matches_and_documented_tie_breakers(
    django_assert_num_queries,
):
    owner, _, organization, league, season, teams, _ = make_data()
    make_finished_match(season, teams[0], teams[1], 2, 1)
    make_finished_match(season, teams[0], teams[2], 0, 0)
    live_fixture = Fixture.objects.create(
        season=season,
        home_team=teams[1],
        away_team=teams[2],
        round_number=2,
    )
    Match.objects.create(
        fixture=live_fixture,
        status=Match.Status.LIVE,
        home_score=4,
        away_score=0,
    )

    with django_assert_num_queries(3):
        standings = get_season_standings(season)

    assert standings == [
        {
            "team_id": teams[0].id,
            "team_name": "Alpha",
            "mp": 2,
            "wins": 1,
            "draws": 1,
            "losses": 0,
            "gf": 2,
            "ga": 1,
            "gd": 1,
            "pts": 4,
        },
        {
            "team_id": teams[2].id,
            "team_name": "Charlie",
            "mp": 1,
            "wins": 0,
            "draws": 1,
            "losses": 0,
            "gf": 0,
            "ga": 0,
            "gd": 0,
            "pts": 1,
        },
        {
            "team_id": teams[1].id,
            "team_name": "Bravo",
            "mp": 1,
            "wins": 0,
            "draws": 0,
            "losses": 1,
            "gf": 1,
            "ga": 2,
            "gd": -1,
            "pts": 0,
        },
    ]

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.get(season_url(organization, league, season, "standings/"))
    assert response.status_code == 200
    assert response.data[0]["team_name"] == "Alpha"
    assert response.data[0]["pts"] == 4


@pytest.mark.django_db
def test_player_statistics_and_top_scorers_only_use_finished_events():
    _, _, organization, league, season, teams, players = make_data()
    match = make_finished_match(season, teams[0], teams[1], 2, 1)
    MatchEvent.objects.create(
        match=match,
        event_type=MatchEvent.EventType.GOAL,
        minute=10,
        team=teams[0],
        player=players[0],
    )
    MatchEvent.objects.create(
        match=match,
        event_type=MatchEvent.EventType.GOAL,
        minute=20,
        team=teams[0],
        player=players[0],
    )
    MatchEvent.objects.create(
        match=match,
        event_type=MatchEvent.EventType.YELLOW_CARD,
        minute=30,
        team=teams[0],
        player=players[0],
    )
    MatchEvent.objects.create(
        match=match,
        event_type=MatchEvent.EventType.RED_CARD,
        minute=70,
        team=teams[1],
        player=players[1],
    )
    live_fixture = Fixture.objects.create(
        season=season,
        home_team=teams[1],
        away_team=teams[2],
        round_number=2,
    )
    live_match = Match.objects.create(fixture=live_fixture, status=Match.Status.LIVE)
    MatchEvent.objects.create(
        match=live_match,
        event_type=MatchEvent.EventType.GOAL,
        minute=5,
        team=teams[1],
        player=players[1],
    )

    stats = list(get_season_player_statistics(season, organization))
    assert stats[0].id == players[0].id
    assert stats[0].goals == 2
    assert stats[0].yellow_cards == 1
    assert stats[0].red_cards == 0
    assert stats[1].id == players[1].id
    assert stats[1].goals == 0
    assert stats[1].red_cards == 1

    client = APIClient()
    client.force_authenticate(user=organization.created_by)
    response = client.get(season_url(organization, league, season, "statistics/top-scorers/"))
    assert response.status_code == 200
    assert response.data[0]["id"] == players[0].id
    assert len(response.data) == 3

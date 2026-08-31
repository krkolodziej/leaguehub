import pytest
from django.core.management import call_command

from apps.competitions.management.commands.seed_demo import (
    DEMO_USERS,
    LEGACY_ORGANIZATION_SLUGS,
    LEGACY_USER_EMAILS,
    ORGANIZATION_SLUG,
    TEAM_SPECS,
)
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
from apps.competitions.services.standings import get_season_standings
from apps.matches.models import Match, MatchEvent
from apps.organizations.models import Organization, OrganizationMembership

SEEDED_MODELS = (
    Organization,
    OrganizationMembership,
    League,
    Season,
    Team,
    SeasonTeam,
    Player,
    RosterEntry,
    Fixture,
    Match,
    MatchEvent,
)


def _counts():
    return tuple(model.objects.count() for model in SEEDED_MODELS)


@pytest.fixture
def seeded_season(db):
    call_command("seed_demo", verbosity=0)
    return Season.objects.get(league__organization__slug=ORGANIZATION_SLUG)


@pytest.mark.django_db
def test_seed_demo_builds_a_full_season_on_an_empty_database():
    call_command("seed_demo", verbosity=0)

    organization = Organization.objects.get(slug=ORGANIZATION_SLUG)
    season = Season.objects.get(league__organization=organization)
    matches = Match.objects.filter(fixture__season=season)

    assert SeasonTeam.objects.filter(season=season).count() == len(TEAM_SPECS)
    # A full double round robin between twelve clubs.
    assert Fixture.objects.filter(season=season).count() == 132
    assert matches.count() == 132
    assert matches.filter(status=Match.Status.LIVE).count() == 1
    assert matches.filter(status=Match.Status.SCHEDULED).exists()
    assert (
        matches.filter(
            status__in=(Match.Status.CANCELLED, Match.Status.POSTPONED)
        ).count()
        == 3
    )

    memberships = OrganizationMembership.objects.filter(organization=organization)
    assert {membership.role for membership in memberships} == {
        spec.role for spec in DEMO_USERS
    }


@pytest.mark.django_db
def test_seed_demo_gives_every_club_a_squad(seeded_season):
    for season_team in SeasonTeam.objects.filter(season=seeded_season):
        roster = RosterEntry.objects.filter(season_team=season_team)
        assert 16 <= roster.count() <= 18
        assert roster.filter(is_captain=True).count() == 1


@pytest.mark.django_db
def test_running_seed_demo_twice_does_not_duplicate_data():
    call_command("seed_demo", verbosity=0)
    before = _counts()

    call_command("seed_demo", verbosity=0)

    assert _counts() == before


@pytest.mark.django_db
def test_flush_rebuilds_the_dataset_without_duplicating_it():
    call_command("seed_demo", verbosity=0)
    before = _counts()

    call_command("seed_demo", "--flush", verbosity=0)

    assert _counts() == before


@pytest.mark.django_db
def test_flush_also_clears_data_left_by_the_previous_seed_command():
    owner = User.objects.create_user(LEGACY_USER_EMAILS[0], "irrelevant")
    legacy = Organization.objects.create(
        name="Demo League", slug=LEGACY_ORGANIZATION_SLUGS[0], created_by=owner
    )
    League.objects.create(organization=legacy, name="Demo Division", slug="demo-division")

    call_command("seed_demo", "--flush", verbosity=0)

    assert not Organization.objects.filter(slug=LEGACY_ORGANIZATION_SLUGS[0]).exists()
    assert not User.objects.filter(email=LEGACY_USER_EMAILS[0]).exists()
    assert Organization.objects.filter(slug=ORGANIZATION_SLUG).exists()


@pytest.mark.django_db
def test_finished_match_scores_match_their_goal_events(seeded_season):
    finished = Match.objects.filter(
        fixture__season=seeded_season, status=Match.Status.FINISHED
    ).select_related("fixture")
    assert finished.exists()

    for match in finished:
        goals = MatchEvent.objects.filter(
            match=match, event_type=MatchEvent.EventType.GOAL
        )
        home_goals = goals.filter(team_id=match.fixture.home_team_id).count()
        away_goals = goals.filter(team_id=match.fixture.away_team_id).count()
        assert (home_goals, away_goals) == (match.home_score, match.away_score)


@pytest.mark.django_db
def test_every_goal_is_credited_to_a_rostered_player(seeded_season):
    for event in MatchEvent.objects.filter(
        match__fixture__season=seeded_season
    ).select_related("match__fixture"):
        assert RosterEntry.objects.filter(
            season_team__season=seeded_season,
            season_team__team_id=event.team_id,
            player_id=event.player_id,
        ).exists()


@pytest.mark.django_db
def test_standings_agree_with_the_finished_results(seeded_season):
    standings = get_season_standings(seeded_season)
    assert len(standings) == len(TEAM_SPECS)

    finished = Match.objects.filter(
        fixture__season=seeded_season, status=Match.Status.FINISHED
    ).select_related("fixture")
    expected = {row["team_id"]: {"pts": 0, "mp": 0} for row in standings}
    for match in finished:
        home_id = match.fixture.home_team_id
        away_id = match.fixture.away_team_id
        expected[home_id]["mp"] += 1
        expected[away_id]["mp"] += 1
        if match.home_score > match.away_score:
            expected[home_id]["pts"] += 3
        elif match.home_score < match.away_score:
            expected[away_id]["pts"] += 3
        else:
            expected[home_id]["pts"] += 1
            expected[away_id]["pts"] += 1

    for row in standings:
        assert row["pts"] == expected[row["team_id"]]["pts"]
        assert row["mp"] == expected[row["team_id"]]["mp"]
        assert row["pts"] == 3 * row["wins"] + row["draws"]
        assert row["mp"] == row["wins"] + row["draws"] + row["losses"]

    # A credible table needs a spread, not twelve clubs on the same points.
    assert standings[0]["pts"] > standings[-1]["pts"]

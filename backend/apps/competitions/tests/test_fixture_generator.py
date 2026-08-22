import pytest

from apps.competitions.services.fixture_generator import (
    FixtureGenerationError,
    generate_round_robin_pairings,
)


def test_single_round_robin_is_deterministic_and_covers_each_pair_once():
    first = generate_round_robin_pairings([4, 1, 3, 2])
    second = generate_round_robin_pairings([1, 2, 3, 4])

    pairings = {(fixture.home_team_id, fixture.away_team_id) for fixture in first}
    unordered_pairs = {
        frozenset((fixture.home_team_id, fixture.away_team_id)) for fixture in first
    }

    assert first == second
    assert len(first) == 6
    assert len(pairings) == 6
    assert len(unordered_pairs) == 6
    assert {fixture.round_number for fixture in first} == {1, 2, 3}
    assert all(fixture.home_team_id != fixture.away_team_id for fixture in first)


def test_double_round_robin_reverses_home_and_away():
    fixtures = generate_round_robin_pairings([1, 2, 3, 4], double_round_robin=True)
    directions = {(fixture.home_team_id, fixture.away_team_id) for fixture in fixtures}
    unordered_pairs = {
        frozenset((fixture.home_team_id, fixture.away_team_id)) for fixture in fixtures
    }

    assert len(fixtures) == 12
    assert len(directions) == 12
    assert len(unordered_pairs) == 6
    assert {fixture.leg for fixture in fixtures} == {1, 2}
    assert {fixture.round_number for fixture in fixtures} == {1, 2, 3, 4, 5, 6}
    for home_team_id, away_team_id in directions:
        assert (away_team_id, home_team_id) in directions


def test_odd_number_of_teams_uses_byes_without_duplicate_pairings():
    fixtures = generate_round_robin_pairings([1, 2, 3, 4, 5])
    unordered_pairs = {
        frozenset((fixture.home_team_id, fixture.away_team_id)) for fixture in fixtures
    }

    appearances = {team_id: 0 for team_id in range(1, 6)}
    for fixture in fixtures:
        appearances[fixture.home_team_id] += 1
        appearances[fixture.away_team_id] += 1

    assert len(fixtures) == 10
    assert len(unordered_pairs) == 10
    assert set(appearances.values()) == {4}


@pytest.mark.parametrize("team_ids", [[], [1], [1, 1]])
def test_invalid_team_input_is_rejected(team_ids):
    with pytest.raises(FixtureGenerationError):
        generate_round_robin_pairings(team_ids)

from dataclasses import dataclass

from django.db import transaction

from ..models import Fixture, Season, SeasonTeam


class FixtureGenerationError(ValueError):
    """Base error for invalid fixture generation requests."""


class FixturesAlreadyGenerated(FixtureGenerationError):
    """Raised when a season already has at least one fixture."""


@dataclass(frozen=True)
class FixturePairing:
    round_number: int
    leg: int
    home_team_id: int
    away_team_id: int


def generate_round_robin_pairings(
    team_ids: list[int] | tuple[int, ...],
    *,
    double_round_robin: bool = False,
) -> list[FixturePairing]:
    """Return a deterministic circle-method schedule without touching the DB."""
    normalized_team_ids = tuple(sorted(team_ids))
    if len(normalized_team_ids) < 2:
        raise FixtureGenerationError("At least two teams are required.")
    if len(set(normalized_team_ids)) != len(normalized_team_ids):
        raise FixtureGenerationError("Team IDs must be unique.")

    rotation = list(normalized_team_ids)
    if len(rotation) % 2:
        rotation.append(None)

    teams_per_round = len(rotation) // 2
    round_count = len(rotation) - 1
    first_leg: list[FixturePairing] = []

    for round_index in range(round_count):
        for pair_index in range(teams_per_round):
            first = rotation[pair_index]
            second = rotation[-pair_index - 1]
            if first is None or second is None:
                continue

            if (round_index + pair_index) % 2:
                home_team_id, away_team_id = second, first
            else:
                home_team_id, away_team_id = first, second
            first_leg.append(
                FixturePairing(
                    round_number=round_index + 1,
                    leg=1,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                )
            )

        # Keep the first team fixed and rotate every other team clockwise.
        rotation = [rotation[0], rotation[-1], *rotation[1:-1]]

    if not double_round_robin:
        return first_leg

    second_leg = [
        FixturePairing(
            round_number=pairing.round_number + round_count,
            leg=2,
            home_team_id=pairing.away_team_id,
            away_team_id=pairing.home_team_id,
        )
        for pairing in first_leg
    ]
    return first_leg + second_leg


class RoundRobinFixtureGenerator:
    """Persist a deterministic round-robin schedule for one season."""

    @classmethod
    def generate_for_season(
        cls,
        season: Season,
        *,
        double_round_robin: bool = False,
    ) -> list[Fixture]:
        with transaction.atomic():
            locked_season = Season.objects.select_for_update().get(pk=season.pk)
            if Fixture.objects.filter(season=locked_season).exists():
                raise FixturesAlreadyGenerated(
                    "Fixtures have already been generated for this season."
                )

            team_ids = list(
                SeasonTeam.objects.filter(season=locked_season)
                .order_by("team_id")
                .values_list("team_id", flat=True)
            )
            pairings = generate_round_robin_pairings(
                team_ids,
                double_round_robin=double_round_robin,
            )
            Fixture.objects.bulk_create(
                [
                    Fixture(
                        season=locked_season,
                        home_team_id=pairing.home_team_id,
                        away_team_id=pairing.away_team_id,
                        round_number=pairing.round_number,
                        leg=pairing.leg,
                    )
                    for pairing in pairings
                ]
            )

            return list(
                Fixture.objects.filter(season=locked_season)
                .select_related("home_team", "away_team")
                .order_by("round_number", "leg", "id")
            )

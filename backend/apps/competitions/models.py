from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimestampedModel
from apps.organizations.models import Organization


class League(TimestampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="leagues",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "slug"],
                name="unique_league_slug_per_organization",
            ),
        ]

    def __str__(self):
        return self.name


class Season(TimestampedModel):
    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name="seasons",
    )
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date", "name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["league", "name"],
                name="unique_season_name_per_league",
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=models.F("start_date")),
                name="season_end_on_or_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.league} - {self.name}"


class Team(TimestampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="teams",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "slug"],
                name="unique_team_slug_per_organization",
            ),
        ]

    def __str__(self):
        return self.name


class SeasonTeam(TimestampedModel):
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="season_teams",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="season_appearances",
    )

    class Meta:
        ordering = ["season_id", "team__name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["season", "team"],
                name="unique_team_per_season",
            ),
        ]

    def clean(self):
        super().clean()
        if self.season_id and self.team_id:
            if self.season.league.organization_id != self.team.organization_id:
                raise ValidationError(
                    "Season and team must belong to the same organization."
                )

    def __str__(self):
        return f"{self.team} in {self.season}"


class Player(TimestampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="players",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name", "id"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.full_name


class RosterEntry(TimestampedModel):
    season_team = models.ForeignKey(
        SeasonTeam,
        on_delete=models.CASCADE,
        related_name="roster_entries",
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="roster_entries",
    )
    shirt_number = models.PositiveSmallIntegerField(null=True, blank=True)
    position = models.CharField(max_length=50, blank=True)
    is_captain = models.BooleanField(default=False)

    class Meta:
        ordering = ["season_team_id", "shirt_number", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["season_team", "player"],
                name="unique_player_per_season_team",
            ),
            models.UniqueConstraint(
                fields=["season_team", "shirt_number"],
                condition=models.Q(shirt_number__isnull=False),
                name="unique_shirt_number_per_season_team",
            ),
            models.UniqueConstraint(
                fields=["season_team"],
                condition=models.Q(is_captain=True),
                name="one_captain_per_season_team",
            ),
        ]

    def clean(self):
        super().clean()
        if self.season_team_id and self.player_id:
            if (
                self.season_team.season.league.organization_id
                != self.player.organization_id
            ):
                raise ValidationError(
                    "Season team and player must belong to the same organization."
                )

    def __str__(self):
        return f"{self.player} - {self.season_team}"


class Fixture(TimestampedModel):
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="fixtures",
    )
    home_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="home_fixtures",
    )
    away_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="away_fixtures",
    )
    round_number = models.PositiveIntegerField()
    leg = models.PositiveSmallIntegerField(default=1)
    scheduled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["season_id", "round_number", "leg", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["season", "home_team", "away_team"],
                name="unique_fixture_direction_per_season",
            ),
            models.CheckConstraint(
                condition=~models.Q(home_team=models.F("away_team")),
                name="fixture_home_and_away_must_differ",
            ),
            models.CheckConstraint(
                condition=models.Q(leg__in=[1, 2]),
                name="fixture_leg_must_be_one_or_two",
            ),
        ]

    def clean(self):
        super().clean()
        if self.home_team_id and self.away_team_id:
            if self.home_team_id == self.away_team_id:
                raise ValidationError("Home and away teams must be different.")
            if self.home_team.organization_id != self.away_team.organization_id:
                raise ValidationError(
                    "Home and away teams must belong to the same organization."
                )
        if self.season_id and self.home_team_id and self.away_team_id:
            organization_id = self.season.league.organization_id
            if (
                self.home_team.organization_id != organization_id
                or self.away_team.organization_id != organization_id
            ):
                raise ValidationError(
                    "Fixture teams must belong to the season organization."
                )

    def __str__(self):
        return f"Round {self.round_number}: {self.home_team} vs {self.away_team}"

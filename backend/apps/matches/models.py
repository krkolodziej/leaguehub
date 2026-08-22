from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimestampedModel
from apps.competitions.models import Fixture, Player, Team


class Match(TimestampedModel):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        LIVE = "LIVE", "Live"
        FINISHED = "FINISHED", "Finished"
        CANCELLED = "CANCELLED", "Cancelled"
        POSTPONED = "POSTPONED", "Postponed"

    fixture = models.OneToOneField(
        Fixture,
        on_delete=models.CASCADE,
        related_name="match",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    home_score = models.PositiveSmallIntegerField(default=0)
    away_score = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["fixture__round_number", "fixture__leg", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    status__in=["SCHEDULED", "LIVE", "FINISHED", "CANCELLED", "POSTPONED"]
                ),
                name="valid_match_status",
            ),
        ]

    def clean(self):
        super().clean()
        if self.finished_at and self.started_at and self.finished_at < self.started_at:
            raise ValidationError("A match cannot finish before it starts.")

    def __str__(self):
        return f"{self.fixture} ({self.get_status_display()})"


class MatchEvent(TimestampedModel):
    class EventType(models.TextChoices):
        GOAL = "GOAL", "Goal"
        YELLOW_CARD = "YELLOW_CARD", "Yellow card"
        RED_CARD = "RED_CARD", "Red card"
        SUBSTITUTION = "SUBSTITUTION", "Substitution"

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    minute = models.PositiveSmallIntegerField()
    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name="match_events",
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.PROTECT,
        related_name="match_events",
    )
    related_player = models.ForeignKey(
        Player,
        on_delete=models.PROTECT,
        related_name="substitution_events_in",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["minute", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(minute__gte=1) & models.Q(minute__lte=180),
                name="match_event_minute_between_one_and_180",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    event_type__in=["GOAL", "YELLOW_CARD", "RED_CARD", "SUBSTITUTION"]
                ),
                name="valid_match_event_type",
            ),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} {self.minute}' - {self.match}"

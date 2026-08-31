from dataclasses import dataclass
import logging

from django.db import transaction
from django.utils import timezone

from apps.competitions.models import Fixture, Player, RosterEntry, Team

from .models import Match, MatchEvent
from .realtime import schedule_match_update

logger = logging.getLogger(__name__)


def _enqueue_match_finished_notification(match_id: int) -> None:
    from apps.notifications.tasks import notify_match_finished

    try:
        notify_match_finished.delay(match_id)
    except Exception:  # pragma: no cover - broker availability is operational
        logger.exception("Could not enqueue finished-match notification")


class MatchLifecycleError(Exception):
    """Raised when a match transition is not allowed."""


class MatchEventError(Exception):
    """Raised when an event violates match or roster rules."""


@dataclass(frozen=True)
class MatchTransition:
    status: Match.Status
    timestamp_field: str | None


ALLOWED_TRANSITIONS = {
    Match.Status.SCHEDULED: {
        Match.Status.LIVE,
        Match.Status.CANCELLED,
        Match.Status.POSTPONED,
    },
    Match.Status.POSTPONED: {
        Match.Status.SCHEDULED,
        Match.Status.LIVE,
        Match.Status.CANCELLED,
    },
    Match.Status.LIVE: {
        Match.Status.FINISHED,
        Match.Status.CANCELLED,
        Match.Status.POSTPONED,
    },
    Match.Status.FINISHED: set(),
    Match.Status.CANCELLED: set(),
}


def create_match_from_fixture(fixture: Fixture) -> Match:
    with transaction.atomic():
        locked_fixture = Fixture.objects.select_for_update().get(pk=fixture.pk)
        if Match.objects.filter(fixture=locked_fixture).exists():
            raise MatchLifecycleError("A match already exists for this fixture.")
        match = Match.objects.create(fixture=locked_fixture)
        schedule_match_update(match.pk)
        return match


def transition_match(match: Match, target_status: Match.Status) -> Match:
    with transaction.atomic():
        locked_match = Match.objects.select_for_update().get(
            pk=match.pk,
            )
        if target_status not in ALLOWED_TRANSITIONS[locked_match.status]:
            raise MatchLifecycleError(
                f"Cannot transition match from {locked_match.status} to {target_status}."
            )
        now = timezone.now()
        locked_match.status = target_status
        if target_status == Match.Status.LIVE:
            locked_match.started_at = locked_match.started_at or now
        if target_status == Match.Status.FINISHED:
            locked_match.finished_at = now
        locked_match.save(update_fields=["status", "started_at", "finished_at", "updated_at"])
        schedule_match_update(locked_match.pk)
        if target_status == Match.Status.FINISHED:
            transaction.on_commit(
                lambda: _enqueue_match_finished_notification(locked_match.pk)
            )
        return locked_match


def start_match(match: Match) -> Match:
    return transition_match(match, Match.Status.LIVE)


def finish_match(match: Match) -> Match:
    return transition_match(match, Match.Status.FINISHED)


def cancel_match(match: Match) -> Match:
    return transition_match(match, Match.Status.CANCELLED)


def postpone_match(match: Match) -> Match:
    return transition_match(match, Match.Status.POSTPONED)


def _validate_rostered_player(match: Match, team: Team, player: Player) -> None:
    if not RosterEntry.objects.filter(
        season_team__season_id=match.fixture.season_id,
        season_team__team_id=team.pk,
        player=player,
    ).exists():
        raise MatchEventError("Player is not rostered for this team and season.")


def add_match_event(
    match: Match,
    *,
    event_type: str,
    minute: int,
    team: Team,
    player: Player,
    related_player: Player | None = None,
) -> MatchEvent:
    with transaction.atomic():
        locked_match = Match.objects.select_for_update().select_related(
            "fixture__season", "fixture__home_team", "fixture__away_team"
        ).get(pk=match.pk)
        if locked_match.status != Match.Status.LIVE:
            raise MatchEventError("Events can only be added while a match is live.")
        if team.pk not in {
            locked_match.fixture.home_team_id,
            locked_match.fixture.away_team_id,
        }:
            raise MatchEventError("Event team must participate in this fixture.")
        if not 1 <= minute <= 180:
            raise MatchEventError("Event minute must be between 1 and 180.")
        try:
            event_enum = MatchEvent.EventType(event_type)
        except ValueError as exc:
            raise MatchEventError("Unsupported match event type.") from exc
        _validate_rostered_player(locked_match, team, player)
        if event_enum == MatchEvent.EventType.SUBSTITUTION:
            if related_player is None or related_player.pk == player.pk:
                raise MatchEventError(
                    "Substitutions require two different rostered players."
                )
            _validate_rostered_player(locked_match, team, related_player)
        elif related_player is not None:
            raise MatchEventError(
                "Only substitution events can include a related player."
            )
        event = MatchEvent.objects.create(
            match=locked_match,
            event_type=event_enum,
            minute=minute,
            team=team,
            player=player,
            related_player=related_player,
        )
        if event_enum == MatchEvent.EventType.GOAL:
            score_field = (
                "home_score"
                if team.pk == locked_match.fixture.home_team_id
                else "away_score"
            )
            setattr(locked_match, score_field, getattr(locked_match, score_field) + 1)
            locked_match.save(update_fields=[score_field, "updated_at"])
        schedule_match_update(locked_match.pk, event_id=event.pk)
        return event

"""Best-effort publication of committed match changes to WebSocket viewers."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

logger = logging.getLogger(__name__)


def match_group_name(match_id: int) -> str:
    return f"match-{match_id}"


def schedule_match_update(match_id: int, *, event_id: int | None = None) -> None:
    """Publish only after the surrounding transaction commits successfully."""

    transaction.on_commit(
        lambda: publish_match_update(match_id, event_id=event_id)
    )


def get_match_snapshot(match_id: int) -> dict:
    from .models import Match

    match = Match.objects.select_related(
        "fixture__home_team", "fixture__away_team"
    ).get(pk=match_id)
    return {
        "id": match.id,
        "fixture_id": match.fixture_id,
        "season_id": match.fixture.season_id,
        "home_team_id": match.fixture.home_team_id,
        "home_team_name": match.fixture.home_team.name,
        "away_team_id": match.fixture.away_team_id,
        "away_team_name": match.fixture.away_team.name,
        "status": match.status,
        "home_score": match.home_score,
        "away_score": match.away_score,
        "started_at": match.started_at.isoformat() if match.started_at else None,
        "finished_at": match.finished_at.isoformat() if match.finished_at else None,
    }


def _event_snapshot(event_id: int) -> dict:
    from .models import MatchEvent

    event = MatchEvent.objects.get(pk=event_id)
    return {
        "id": event.id,
        "event_type": event.event_type,
        "minute": event.minute,
        "team_id": event.team_id,
        "player_id": event.player_id,
        "related_player_id": event.related_player_id,
    }


def publish_match_update(match_id: int, *, event_id: int | None = None) -> None:
    """Send a snapshot to every viewer; Redis failures never break an HTTP command."""

    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        payload = {"type": "match.updated", "match": get_match_snapshot(match_id)}
        if event_id is not None:
            payload["event"] = _event_snapshot(event_id)
        async_to_sync(channel_layer.group_send)(
            match_group_name(match_id),
            {"type": "match.update", "payload": payload},
        )
    except Exception:  # pragma: no cover - infrastructure failure is best effort
        logger.exception("Could not publish realtime update for match %s", match_id)

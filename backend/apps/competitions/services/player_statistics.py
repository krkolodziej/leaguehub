from django.db.models import Count, Q

from apps.competitions.models import Player
from apps.matches.models import Match, MatchEvent


def get_season_player_statistics(season, organization):
    """Return event-derived player statistics for players in the season.

    Appearances are intentionally omitted: Stage 6 does not store lineups or
    minutes played, so counting event participants would be misleading.
    """
    finished_event = Q(
        match_events__match__fixture__season=season,
        match_events__match__status=Match.Status.FINISHED,
    )
    players = (
        Player.objects.filter(
            organization=organization,
            roster_entries__season_team__season=season,
        )
        .distinct()
        .annotate(
            goals=Count(
                "match_events",
                filter=finished_event
                & Q(match_events__event_type=MatchEvent.EventType.GOAL),
                distinct=True,
            ),
            yellow_cards=Count(
                "match_events",
                filter=finished_event
                & Q(match_events__event_type=MatchEvent.EventType.YELLOW_CARD),
                distinct=True,
            ),
            red_cards=Count(
                "match_events",
                filter=finished_event
                & Q(match_events__event_type=MatchEvent.EventType.RED_CARD),
                distinct=True,
            ),
        )
        .order_by("-goals", "-yellow_cards", "last_name", "first_name", "id")
    )
    return players

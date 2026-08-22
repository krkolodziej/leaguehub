from django.urls import path

from .views import (
    CancelMatchView,
    FinishMatchView,
    MatchDetailView,
    MatchEventListCreateView,
    MatchListCreateView,
    PostponeMatchView,
    StartMatchView,
)

urlpatterns = [
    path(
        "organizations/<int:organization_id>/leagues/<int:league_id>/seasons/<int:season_id>/matches/",
        MatchListCreateView.as_view(),
        name="match-list-create",
    ),
    path(
        "organizations/<int:organization_id>/leagues/<int:league_id>/seasons/<int:season_id>/matches/<int:match_id>/",
        MatchDetailView.as_view(),
        name="match-detail",
    ),
    path(
        "organizations/<int:organization_id>/leagues/<int:league_id>/seasons/<int:season_id>/matches/<int:match_id>/start/",
        StartMatchView.as_view(),
        name="match-start",
    ),
    path(
        "organizations/<int:organization_id>/leagues/<int:league_id>/seasons/<int:season_id>/matches/<int:match_id>/finish/",
        FinishMatchView.as_view(),
        name="match-finish",
    ),
    path(
        "organizations/<int:organization_id>/leagues/<int:league_id>/seasons/<int:season_id>/matches/<int:match_id>/cancel/",
        CancelMatchView.as_view(),
        name="match-cancel",
    ),
    path(
        "organizations/<int:organization_id>/leagues/<int:league_id>/seasons/<int:season_id>/matches/<int:match_id>/postpone/",
        PostponeMatchView.as_view(),
        name="match-postpone",
    ),
    path(
        "organizations/<int:organization_id>/leagues/<int:league_id>/seasons/<int:season_id>/matches/<int:match_id>/events/",
        MatchEventListCreateView.as_view(),
        name="match-event-list-create",
    ),
]

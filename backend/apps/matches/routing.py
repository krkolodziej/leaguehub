from django.urls import path

from .consumers import MatchConsumer

websocket_urlpatterns = [
    path(
        "ws/organizations/<int:organization_id>/leagues/<int:league_id>/"
        "seasons/<int:season_id>/matches/<int:match_id>/",
        MatchConsumer.as_asgi(),
    )
]

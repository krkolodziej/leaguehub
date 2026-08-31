from django.urls import path

from .views import MatchReportView

urlpatterns = [
    path(
        "organizations/<int:organization_id>/leagues/<int:league_id>/seasons/<int:season_id>/matches/<int:match_id>/report/",
        MatchReportView.as_view(),
        name="match-report",
    ),
]

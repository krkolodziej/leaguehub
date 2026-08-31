from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matches.views import MatchAccessMixin

from .models import MatchReport
from .serializers import MatchReportSerializer
from .services import build_match_summary
from .tasks import generate_match_report


class MatchReportView(MatchAccessMixin, APIView):
    @extend_schema(responses=MatchReportSerializer)
    def get(self, request, organization_id, league_id, season_id, match_id):
        _, _, match = self.get_match(request, organization_id, league_id, season_id, match_id)
        report = get_object_or_404(MatchReport, match=match)
        return Response(MatchReportSerializer(report).data)

    @extend_schema(responses={202: MatchReportSerializer, 200: MatchReportSerializer})
    def post(self, request, organization_id, league_id, season_id, match_id):
        organization, _, match = self.get_match(request, organization_id, league_id, season_id, match_id)
        self.require_manager(request, organization)
        if match.status != match.Status.FINISHED:
            return Response(
                {"detail": "Reports can only be generated for finished matches.", "code": "conflict"},
                status=status.HTTP_409_CONFLICT,
            )
        report, _ = MatchReport.objects.get_or_create(
            match=match,
            defaults={"summary": build_match_summary(match).as_dict()},
        )
        if report.status == MatchReport.Status.COMPLETED:
            return Response(MatchReportSerializer(report).data)
        report.status = MatchReport.Status.PENDING
        report.summary = build_match_summary(match).as_dict()
        report.error = ""
        report.save(update_fields=["status", "summary", "error", "updated_at"])
        try:
            generate_match_report.delay(match.pk)
        except Exception:
            report.status = MatchReport.Status.FAILED
            report.error = "The report job could not be queued."
            report.save(update_fields=["status", "error", "updated_at"])
            return Response(MatchReportSerializer(report).data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(MatchReportSerializer(report).data, status=status.HTTP_202_ACCEPTED)

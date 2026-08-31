import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.matches.models import Match

from .models import MatchReport
from .services import (
    build_match_summary,
    get_match_report_generator,
    validate_generated_report,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def generate_match_report(self, match_id: int) -> str:
    """Generate a report without ever changing match state or standings."""
    try:
        match = (
            Match.objects.select_related("fixture__home_team", "fixture__away_team")
            .prefetch_related("events__player", "events__team")
            .get(pk=match_id)
        )
    except Match.DoesNotExist:
        return "missing"
    if match.status != Match.Status.FINISHED:
        return "skipped"

    summary = build_match_summary(match)
    report, _ = MatchReport.objects.get_or_create(
        match=match,
        defaults={"status": MatchReport.Status.PENDING, "summary": summary.as_dict()},
    )
    if report.status == MatchReport.Status.COMPLETED:
        return "completed"
    report.status = MatchReport.Status.GENERATING
    report.summary = summary.as_dict()
    report.error = ""
    report.save(update_fields=["status", "summary", "error", "updated_at"])
    try:
        generated = validate_generated_report(get_match_report_generator().generate(summary))
    except Exception as exc:  # provider failures are isolated from match results
        logger.exception("Match report generation failed for match %s", match_id)
        report.status = MatchReport.Status.FAILED
        report.error = str(exc)[:500]
        report.save(update_fields=["status", "error", "updated_at"])
        return "failed"

    with transaction.atomic():
        report.status = MatchReport.Status.COMPLETED
        report.content = generated.text
        report.generated_at = timezone.now()
        report.save(update_fields=["status", "content", "generated_at", "updated_at"])
    return "completed"

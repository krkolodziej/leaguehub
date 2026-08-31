import pytest
from django.core.management import call_command

from apps.ai_reports.models import MatchReport
from apps.ai_reports.tasks import generate_match_report
from apps.matches.models import Match


@pytest.mark.django_db
def test_finished_match_report_is_generated_from_minimal_summary():
    call_command("seed_demo")
    match = Match.objects.filter(status=Match.Status.FINISHED).first()

    assert generate_match_report(match.pk) == "completed"
    report = MatchReport.objects.get(match=match)
    assert report.status == MatchReport.Status.COMPLETED
    assert "victory" in report.content or "drew" in report.content
    assert report.summary["home_score"] == match.home_score


@pytest.mark.django_db
def test_provider_failure_is_isolated_from_match(monkeypatch):
    call_command("seed_demo")
    match = Match.objects.filter(status=Match.Status.FINISHED).first()

    class BrokenProvider:
        def generate(self, summary):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr("apps.ai_reports.tasks.get_match_report_generator", lambda: BrokenProvider())

    assert generate_match_report(match.pk) == "failed"
    assert Match.objects.get(pk=match.pk).status == Match.Status.FINISHED
    assert MatchReport.objects.get(match=match).status == MatchReport.Status.FAILED

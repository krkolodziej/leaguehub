from django.db import models

from apps.common.models import TimestampedModel
from apps.matches.models import Match


class MatchReport(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        GENERATING = "GENERATING", "Generating"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    match = models.OneToOneField(
        Match,
        on_delete=models.CASCADE,
        related_name="ai_report",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    summary = models.JSONField(default=dict)
    content = models.TextField(blank=True)
    error = models.TextField(blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at", "id"]

    def __str__(self):
        return f"Report for match {self.match_id} ({self.get_status_display()})"

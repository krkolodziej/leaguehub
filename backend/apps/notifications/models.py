from django.conf import settings
from django.db import models

from apps.common.models import TimestampedModel


class Notification(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=64)
    title = models.CharField(max_length=200)
    message = models.TextField()
    dedupe_key = models.CharField(max_length=200, unique=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "read_at"], name="notification_user_read_idx"),
        ]

    def __str__(self):
        return f"{self.title} for {self.user}"

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.matches.models import Match
from apps.notifications.models import Notification
from apps.notifications.tasks import notify_match_finished, send_match_reminder

from ...matches.tests.test_matches import make_match_data


@pytest.mark.django_db
def test_finished_notification_task_is_idempotent_and_targets_managers():
    _, member, _, _, _, fixture, _, _ = make_match_data()
    match = Match.objects.create(fixture=fixture, status=Match.Status.FINISHED)

    assert notify_match_finished.run(match.id) == 1
    assert notify_match_finished.run(match.id) == 0
    assert Notification.objects.filter(kind="MATCH_FINISHED").count() == 1
    assert Notification.objects.filter(user=member).count() == 0
    assert Notification.objects.filter(user__email="match-owner@example.com").exists()


@pytest.mark.django_db
def test_match_reminder_task_is_idempotent():
    _, _, _, _, _, fixture, _, _ = make_match_data()
    fixture.scheduled_at = timezone.now() + timedelta(hours=24)
    fixture.save(update_fields=["scheduled_at", "updated_at"])
    match = Match.objects.create(fixture=fixture)

    assert send_match_reminder.run(match.id) == 1
    assert send_match_reminder.run(match.id) == 0
    assert Notification.objects.filter(kind="MATCH_REMINDER").count() == 1


@pytest.mark.django_db
def test_user_can_list_and_mark_only_their_notifications_read():
    owner, member, *_ = make_match_data()
    notification = Notification.objects.create(
        user=owner,
        kind="MATCH_FINISHED",
        title="Match finished",
        message="Home 1–0 Away.",
        dedupe_key="test-owner-notification",
    )
    other = Notification.objects.create(
        user=member,
        kind="MATCH_FINISHED",
        title="Private",
        message="Not for owner.",
        dedupe_key="test-member-notification",
    )
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get("/api/v1/notifications/")
    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [notification.id]

    marked = client.post(f"/api/v1/notifications/{notification.id}/read/")
    assert marked.status_code == 200
    assert marked.data["read_at"] is not None

    forbidden = client.post(f"/api/v1/notifications/{other.id}/read/")
    assert forbidden.status_code == 404

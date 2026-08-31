from datetime import timedelta

from celery import shared_task
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.organizations.models import OrganizationMembership

from .models import Notification


MANAGER_ROLES = [
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
]


def _create_notification(*, user_id: int, kind: str, title: str, message: str, dedupe_key: str) -> bool:
    try:
        with transaction.atomic():
            _, created = Notification.objects.get_or_create(
                dedupe_key=dedupe_key,
                defaults={
                    "user_id": user_id,
                    "kind": kind,
                    "title": title,
                    "message": message,
                },
            )
            return created
    except IntegrityError:
        return False


def _manager_ids(organization_id: int) -> list[int]:
    return list(
        OrganizationMembership.objects.filter(
            organization_id=organization_id,
            role__in=MANAGER_ROLES,
        ).values_list("user_id", flat=True)
    )


@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_match_reminder(self, match_id: int) -> int:
    from apps.matches.models import Match

    try:
        match = Match.objects.select_related(
            "fixture__home_team",
            "fixture__away_team",
            "fixture__season__league",
        ).get(pk=match_id)
    except Match.DoesNotExist:
        return 0
    if match.status != Match.Status.SCHEDULED or match.fixture.scheduled_at is None:
        return 0

    organization_id = match.fixture.season.league.organization_id
    title = "Match reminder"
    message = (
        f"{match.fixture.home_team.name} vs {match.fixture.away_team.name} "
        f"is scheduled for {match.fixture.scheduled_at.isoformat()}."
    )
    created = 0
    for user_id in _manager_ids(organization_id):
        created += _create_notification(
            user_id=user_id,
            kind="MATCH_REMINDER",
            title=title,
            message=message,
            dedupe_key=f"match-reminder:{match_id}:user:{user_id}",
        )
    return created


@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def notify_match_finished(self, match_id: int) -> int:
    from apps.matches.models import Match

    try:
        match = Match.objects.select_related(
            "fixture__home_team",
            "fixture__away_team",
            "fixture__season__league",
        ).get(pk=match_id)
    except Match.DoesNotExist:
        return 0
    if match.status != Match.Status.FINISHED:
        return 0

    organization_id = match.fixture.season.league.organization_id
    title = "Match finished"
    message = (
        f"{match.fixture.home_team.name} {match.home_score}–{match.away_score} "
        f"{match.fixture.away_team.name}."
    )
    created = 0
    for user_id in _manager_ids(organization_id):
        created += _create_notification(
            user_id=user_id,
            kind="MATCH_FINISHED",
            title=title,
            message=message,
            dedupe_key=f"match-finished:{match_id}:user:{user_id}",
        )
    return created


@shared_task
def dispatch_match_reminders() -> int:
    from apps.matches.models import Match

    now = timezone.now()
    start = now + timedelta(hours=23, minutes=45)
    end = now + timedelta(hours=24, minutes=15)
    match_ids = Match.objects.filter(
        status=Match.Status.SCHEDULED,
        fixture__scheduled_at__range=(start, end),
    ).values_list("id", flat=True)
    for match_id in match_ids:
        send_match_reminder.delay(match_id)
    return len(match_ids)

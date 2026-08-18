from django.conf import settings
from django.db import models

from apps.common.models import TimestampedModel


class Organization(TimestampedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organizations",
    )

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class OrganizationMembership(TimestampedModel):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    class Meta:
        ordering = ["organization_id", "user_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="unique_organization_membership",
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=["OWNER", "ADMIN", "MEMBER"]),
                name="valid_organization_membership_role",
            ),
        ]

    def __str__(self):
        return f"{self.user} in {self.organization} ({self.role})"

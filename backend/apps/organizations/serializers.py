from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Organization, OrganizationMembership

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    created_by_id = serializers.IntegerField(read_only=True)
    my_role = serializers.CharField(
        source="current_user_role",
        read_only=True,
        allow_null=True,
        default=None,
    )

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "created_by_id",
            "my_role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by_id",
            "my_role",
            "created_at",
            "updated_at",
        ]


class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ["id", "user_id", "email", "role", "created_at", "updated_at"]
        read_only_fields = [
            "id",
            "user_id",
            "email",
            "created_at",
            "updated_at",
        ]


class MembershipCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.MEMBER,
        ],
        default=OrganizationMembership.Role.MEMBER,
    )

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if not User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("No user with this email exists.")
        return normalized_email


class MembershipRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=[
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.MEMBER,
        ]
    )

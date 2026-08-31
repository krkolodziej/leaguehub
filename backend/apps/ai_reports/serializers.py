from rest_framework import serializers

from .models import MatchReport


class MatchReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchReport
        fields = ["status", "summary", "content", "error", "generated_at", "updated_at"]
        read_only_fields = fields

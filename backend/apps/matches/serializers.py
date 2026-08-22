from rest_framework import serializers

from apps.competitions.models import Fixture, Player, Team

from .models import Match, MatchEvent


class MatchSerializer(serializers.ModelSerializer):
    fixture_id = serializers.IntegerField(read_only=True)
    home_team_id = serializers.IntegerField(source="fixture.home_team_id", read_only=True)
    home_team_name = serializers.CharField(source="fixture.home_team.name", read_only=True)
    away_team_id = serializers.IntegerField(source="fixture.away_team_id", read_only=True)
    away_team_name = serializers.CharField(source="fixture.away_team.name", read_only=True)
    season_id = serializers.IntegerField(source="fixture.season_id", read_only=True)

    class Meta:
        model = Match
        fields = [
            "id", "fixture_id", "season_id", "home_team_id", "home_team_name",
            "away_team_id", "away_team_name", "status", "home_score", "away_score",
            "started_at", "finished_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class MatchCreateSerializer(serializers.Serializer):
    fixture_id = serializers.PrimaryKeyRelatedField(queryset=Fixture.objects.all())


class MatchEventSerializer(serializers.ModelSerializer):
    team_id = serializers.PrimaryKeyRelatedField(source="team", queryset=Team.objects.all())
    player_id = serializers.PrimaryKeyRelatedField(source="player", queryset=Player.objects.all())
    related_player_id = serializers.PrimaryKeyRelatedField(
        source="related_player", queryset=Player.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = MatchEvent
        fields = [
            "id", "match", "event_type", "minute", "team_id", "player_id",
            "related_player_id", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "match", "created_at", "updated_at"]

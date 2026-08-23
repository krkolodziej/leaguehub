from rest_framework import serializers

from .models import Fixture, League, Player, RosterEntry, Season, SeasonTeam, Team


class StandingsSerializer(serializers.Serializer):
    team_id = serializers.IntegerField()
    team_name = serializers.CharField()
    mp = serializers.IntegerField()
    wins = serializers.IntegerField()
    draws = serializers.IntegerField()
    losses = serializers.IntegerField()
    gf = serializers.IntegerField()
    ga = serializers.IntegerField()
    gd = serializers.IntegerField()
    pts = serializers.IntegerField()


class PlayerStatisticsSerializer(serializers.ModelSerializer):
    goals = serializers.IntegerField(read_only=True)
    yellow_cards = serializers.IntegerField(read_only=True)
    red_cards = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Player
        fields = [
            "id",
            "full_name",
            "goals",
            "yellow_cards",
            "red_cards",
        ]


class LeagueSerializer(serializers.ModelSerializer):
    organization_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = League
        fields = [
            "id",
            "organization_id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]


class SeasonSerializer(serializers.ModelSerializer):
    league_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Season
        fields = [
            "id",
            "league_id",
            "name",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "league_id", "created_at", "updated_at"]


class TeamSerializer(serializers.ModelSerializer):
    organization_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Team
        fields = [
            "id",
            "organization_id",
            "name",
            "slug",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]


class PlayerSerializer(serializers.ModelSerializer):
    organization_id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Player
        fields = [
            "id",
            "organization_id",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization_id",
            "full_name",
            "created_at",
            "updated_at",
        ]


class SeasonTeamSerializer(serializers.ModelSerializer):
    season_id = serializers.IntegerField(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(
        source="team",
        queryset=Team.objects.all(),
    )
    team_name = serializers.CharField(source="team.name", read_only=True)

    class Meta:
        model = SeasonTeam
        fields = [
            "id",
            "season_id",
            "team_id",
            "team_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "season_id", "team_name", "created_at", "updated_at"]

    def validate_team_id(self, team):
        organization = self.context["organization"]
        if team.organization_id != organization.id:
            raise serializers.ValidationError(
                "Team does not belong to this organization."
            )
        return team


class RosterEntrySerializer(serializers.ModelSerializer):
    season_team_id = serializers.IntegerField(read_only=True)
    player_id = serializers.PrimaryKeyRelatedField(
        source="player",
        queryset=Player.objects.all(),
    )
    player_name = serializers.CharField(source="player.full_name", read_only=True)

    class Meta:
        model = RosterEntry
        fields = [
            "id",
            "season_team_id",
            "player_id",
            "player_name",
            "shirt_number",
            "position",
            "is_captain",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "season_team_id",
            "player_name",
            "created_at",
            "updated_at",
        ]

    def validate_player_id(self, player):
        organization = self.context["organization"]
        if player.organization_id != organization.id:
            raise serializers.ValidationError(
                "Player does not belong to this organization."
            )
        return player


class FixtureSerializer(serializers.ModelSerializer):
    season_id = serializers.IntegerField(read_only=True)
    home_team_id = serializers.IntegerField(read_only=True)
    home_team_name = serializers.CharField(source="home_team.name", read_only=True)
    away_team_id = serializers.IntegerField(read_only=True)
    away_team_name = serializers.CharField(source="away_team.name", read_only=True)

    class Meta:
        model = Fixture
        fields = [
            "id",
            "season_id",
            "round_number",
            "leg",
            "home_team_id",
            "home_team_name",
            "away_team_id",
            "away_team_name",
            "scheduled_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "season_id",
            "home_team_id",
            "home_team_name",
            "away_team_id",
            "away_team_name",
            "created_at",
            "updated_at",
        ]


class FixtureGenerationSerializer(serializers.Serializer):
    double_round_robin = serializers.BooleanField(default=False)

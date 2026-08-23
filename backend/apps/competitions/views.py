from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import response_for_queryset
from apps.common.query_params import apply_query_options

from apps.organizations.models import Organization
from apps.organizations.permissions import IsOrganizationMember

from .models import League, Player, Season, SeasonTeam, Team
from .permissions import IsCompetitionManager
from .services.fixture_generator import (
    FixtureGenerationError,
    FixturesAlreadyGenerated,
    RoundRobinFixtureGenerator,
)
from .serializers import (
    FixtureGenerationSerializer,
    FixtureSerializer,
    LeagueSerializer,
    PlayerSerializer,
    RosterEntrySerializer,
    SeasonSerializer,
    SeasonTeamSerializer,
    TeamSerializer,
    PlayerStatisticsSerializer,
    StandingsSerializer,
)
from .services.player_statistics import get_season_player_statistics
from .services.standings import get_season_standings


class OrganizationAccessMixin:
    def get_organization(self, request, organization_id):
        organization = get_object_or_404(
            Organization.objects.filter(memberships__user=request.user),
            pk=organization_id,
        )
        self.check_object_permissions(request, organization)
        return organization

    def require_manager(self, request, organization):
        if not IsCompetitionManager().has_object_permission(
            request,
            self,
            organization,
        ):
            raise PermissionDenied(IsCompetitionManager.message)

    def get_league(self, request, organization_id, league_id):
        organization = self.get_organization(request, organization_id)
        league = get_object_or_404(
            League.objects.filter(organization=organization),
            pk=league_id,
        )
        return organization, league

    def get_season(self, request, organization_id, league_id, season_id):
        organization, league = self.get_league(request, organization_id, league_id)
        season = get_object_or_404(
            Season.objects.filter(league=league),
            pk=season_id,
        )
        return organization, league, season

    def get_season_team(
        self,
        request,
        organization_id,
        league_id,
        season_id,
        season_team_id,
    ):
        organization, league, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        season_team = get_object_or_404(
            SeasonTeam.objects.select_related("team", "season"),
            season=season,
            pk=season_team_id,
        )
        return organization, league, season, season_team

    @staticmethod
    def save_with_conflict(serializer, **extra_fields):
        try:
            with transaction.atomic():
                return serializer.save(**extra_fields)
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "The submitted data conflicts with an existing record."}
            ) from exc


class CompetitionScopedAPIView(OrganizationAccessMixin, APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]


class LeagueListCreateView(CompetitionScopedAPIView):
    @extend_schema(responses=LeagueSerializer(many=True))
    def get(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        leagues = apply_query_options(
            organization.leagues.all(),
            request,
            search_fields=("name", "slug"),
            ordering_fields=("name", "slug", "created_at"),
            default_ordering=("name", "id"),
        )
        return response_for_queryset(leagues, request, LeagueSerializer, view=self)

    @extend_schema(request=LeagueSerializer, responses={201: LeagueSerializer})
    def post(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        self.require_manager(request, organization)
        serializer = LeagueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        league = self.save_with_conflict(serializer, organization=organization)
        return Response(LeagueSerializer(league).data, status=status.HTTP_201_CREATED)


class LeagueDetailView(CompetitionScopedAPIView):
    @extend_schema(responses=LeagueSerializer)
    def get(self, request, organization_id, league_id):
        _, league = self.get_league(request, organization_id, league_id)
        return Response(LeagueSerializer(league).data)

    @extend_schema(request=LeagueSerializer, responses=LeagueSerializer)
    def patch(self, request, organization_id, league_id):
        organization, league = self.get_league(request, organization_id, league_id)
        self.require_manager(request, organization)
        serializer = LeagueSerializer(league, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        league = self.save_with_conflict(serializer)
        return Response(LeagueSerializer(league).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, organization_id, league_id):
        organization, league = self.get_league(request, organization_id, league_id)
        self.require_manager(request, organization)
        league.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SeasonListCreateView(CompetitionScopedAPIView):
    @extend_schema(responses=SeasonSerializer(many=True))
    def get(self, request, organization_id, league_id):
        _, league = self.get_league(request, organization_id, league_id)
        seasons = apply_query_options(
            league.seasons.all(),
            request,
            search_fields=("name",),
            ordering_fields=("name", "start_date", "end_date"),
            default_ordering=("-start_date", "name", "id"),
        )
        return response_for_queryset(seasons, request, SeasonSerializer, view=self)

    @extend_schema(request=SeasonSerializer, responses={201: SeasonSerializer})
    def post(self, request, organization_id, league_id):
        organization, league = self.get_league(request, organization_id, league_id)
        self.require_manager(request, organization)
        serializer = SeasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        season = self.save_with_conflict(serializer, league=league)
        return Response(SeasonSerializer(season).data, status=status.HTTP_201_CREATED)


class SeasonDetailView(CompetitionScopedAPIView):
    @extend_schema(responses=SeasonSerializer)
    def get(self, request, organization_id, league_id, season_id):
        _, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        return Response(SeasonSerializer(season).data)

    @extend_schema(request=SeasonSerializer, responses=SeasonSerializer)
    def patch(self, request, organization_id, league_id, season_id):
        organization, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        self.require_manager(request, organization)
        serializer = SeasonSerializer(season, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        season = self.save_with_conflict(serializer)
        return Response(SeasonSerializer(season).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, organization_id, league_id, season_id):
        organization, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        self.require_manager(request, organization)
        season.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamListCreateView(CompetitionScopedAPIView):
    @extend_schema(responses=TeamSerializer(many=True))
    def get(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        teams = apply_query_options(
            organization.teams.all(),
            request,
            search_fields=("name", "slug"),
            ordering_fields=("name", "slug", "created_at"),
            default_ordering=("name", "id"),
        )
        return response_for_queryset(teams, request, TeamSerializer, view=self)

    @extend_schema(request=TeamSerializer, responses={201: TeamSerializer})
    def post(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        self.require_manager(request, organization)
        serializer = TeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = self.save_with_conflict(serializer, organization=organization)
        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)


class TeamDetailView(CompetitionScopedAPIView):
    @extend_schema(responses=TeamSerializer)
    def get(self, request, organization_id, team_id):
        organization = self.get_organization(request, organization_id)
        team = get_object_or_404(Team.objects.filter(organization=organization), pk=team_id)
        return Response(TeamSerializer(team).data)

    @extend_schema(request=TeamSerializer, responses=TeamSerializer)
    def patch(self, request, organization_id, team_id):
        organization = self.get_organization(request, organization_id)
        self.require_manager(request, organization)
        team = get_object_or_404(Team.objects.filter(organization=organization), pk=team_id)
        serializer = TeamSerializer(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        team = self.save_with_conflict(serializer)
        return Response(TeamSerializer(team).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, organization_id, team_id):
        organization = self.get_organization(request, organization_id)
        self.require_manager(request, organization)
        team = get_object_or_404(Team.objects.filter(organization=organization), pk=team_id)
        team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlayerListCreateView(CompetitionScopedAPIView):
    @extend_schema(responses=PlayerSerializer(many=True))
    def get(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        players = apply_query_options(
            organization.players.all(),
            request,
            search_fields=("first_name", "last_name"),
            ordering_fields=("first_name", "last_name", "date_of_birth"),
            default_ordering=("last_name", "first_name", "id"),
        )
        return response_for_queryset(players, request, PlayerSerializer, view=self)

    @extend_schema(request=PlayerSerializer, responses={201: PlayerSerializer})
    def post(self, request, organization_id):
        organization = self.get_organization(request, organization_id)
        self.require_manager(request, organization)
        serializer = PlayerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        player = self.save_with_conflict(serializer, organization=organization)
        return Response(PlayerSerializer(player).data, status=status.HTTP_201_CREATED)


class PlayerDetailView(CompetitionScopedAPIView):
    @extend_schema(responses=PlayerSerializer)
    def get(self, request, organization_id, player_id):
        organization = self.get_organization(request, organization_id)
        player = get_object_or_404(
            Player.objects.filter(organization=organization),
            pk=player_id,
        )
        return Response(PlayerSerializer(player).data)

    @extend_schema(request=PlayerSerializer, responses=PlayerSerializer)
    def patch(self, request, organization_id, player_id):
        organization = self.get_organization(request, organization_id)
        self.require_manager(request, organization)
        player = get_object_or_404(
            Player.objects.filter(organization=organization),
            pk=player_id,
        )
        serializer = PlayerSerializer(player, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        player = self.save_with_conflict(serializer)
        return Response(PlayerSerializer(player).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, organization_id, player_id):
        organization = self.get_organization(request, organization_id)
        self.require_manager(request, organization)
        player = get_object_or_404(
            Player.objects.filter(organization=organization),
            pk=player_id,
        )
        player.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SeasonTeamListCreateView(CompetitionScopedAPIView):
    @extend_schema(responses=SeasonTeamSerializer(many=True))
    def get(self, request, organization_id, league_id, season_id):
        _, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        season_teams = apply_query_options(
            season.season_teams.select_related("team").all(),
            request,
            search_fields=("team__name", "team__slug"),
            ordering_fields=("team__name", "created_at"),
            default_ordering=("team__name", "id"),
        )
        return response_for_queryset(
            season_teams,
            request,
            SeasonTeamSerializer,
            view=self,
        )

    @extend_schema(
        request=SeasonTeamSerializer,
        responses={201: SeasonTeamSerializer},
    )
    def post(self, request, organization_id, league_id, season_id):
        organization, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        self.require_manager(request, organization)
        serializer = SeasonTeamSerializer(
            data=request.data,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        season_team = self.save_with_conflict(serializer, season=season)
        return Response(
            SeasonTeamSerializer(season_team).data,
            status=status.HTTP_201_CREATED,
        )


class SeasonTeamDetailView(CompetitionScopedAPIView):
    @extend_schema(responses=SeasonTeamSerializer)
    def get(self, request, organization_id, league_id, season_id, season_team_id):
        _, _, _, season_team = self.get_season_team(
            request,
            organization_id,
            league_id,
            season_id,
            season_team_id,
        )
        return Response(SeasonTeamSerializer(season_team).data)

    @extend_schema(
        request=SeasonTeamSerializer,
        responses=SeasonTeamSerializer,
    )
    def patch(self, request, organization_id, league_id, season_id, season_team_id):
        organization, _, season, season_team = self.get_season_team(
            request,
            organization_id,
            league_id,
            season_id,
            season_team_id,
        )
        self.require_manager(request, organization)
        serializer = SeasonTeamSerializer(
            season_team,
            data=request.data,
            partial=True,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        season_team = self.save_with_conflict(serializer, season=season)
        return Response(SeasonTeamSerializer(season_team).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, organization_id, league_id, season_id, season_team_id):
        organization, _, _, season_team = self.get_season_team(
            request,
            organization_id,
            league_id,
            season_id,
            season_team_id,
        )
        self.require_manager(request, organization)
        season_team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RosterListCreateView(CompetitionScopedAPIView):
    @extend_schema(responses=RosterEntrySerializer(many=True))
    def get(
        self,
        request,
        organization_id,
        league_id,
        season_id,
        season_team_id,
    ):
        _, _, _, season_team = self.get_season_team(
            request,
            organization_id,
            league_id,
            season_id,
            season_team_id,
        )
        entries = apply_query_options(
            season_team.roster_entries.select_related("player").all(),
            request,
            search_fields=("player__first_name", "player__last_name", "position"),
            ordering_fields=("shirt_number", "position", "created_at"),
            default_ordering=("shirt_number", "id"),
        )
        return response_for_queryset(
            entries,
            request,
            RosterEntrySerializer,
            view=self,
        )

    @extend_schema(
        request=RosterEntrySerializer,
        responses={201: RosterEntrySerializer},
    )
    def post(
        self,
        request,
        organization_id,
        league_id,
        season_id,
        season_team_id,
    ):
        organization, _, _, season_team = self.get_season_team(
            request,
            organization_id,
            league_id,
            season_id,
            season_team_id,
        )
        self.require_manager(request, organization)
        serializer = RosterEntrySerializer(
            data=request.data,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        entry = self.save_with_conflict(serializer, season_team=season_team)
        return Response(
            RosterEntrySerializer(entry).data,
            status=status.HTTP_201_CREATED,
        )


class RosterDetailView(CompetitionScopedAPIView):
    @extend_schema(responses=RosterEntrySerializer)
    def get(
        self,
        request,
        organization_id,
        league_id,
        season_id,
        season_team_id,
        roster_entry_id,
    ):
        _, _, _, season_team = self.get_season_team(
            request,
            organization_id,
            league_id,
            season_id,
            season_team_id,
        )
        entry = get_object_or_404(
            season_team.roster_entries.select_related("player"),
            pk=roster_entry_id,
        )
        return Response(RosterEntrySerializer(entry).data)

    @extend_schema(
        request=RosterEntrySerializer,
        responses=RosterEntrySerializer,
    )
    def patch(
        self,
        request,
        organization_id,
        league_id,
        season_id,
        season_team_id,
        roster_entry_id,
    ):
        organization, _, _, season_team = self.get_season_team(
            request,
            organization_id,
            league_id,
            season_id,
            season_team_id,
        )
        self.require_manager(request, organization)
        entry = get_object_or_404(
            season_team.roster_entries.select_related("player"),
            pk=roster_entry_id,
        )
        serializer = RosterEntrySerializer(
            entry,
            data=request.data,
            partial=True,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        entry = self.save_with_conflict(serializer)
        return Response(RosterEntrySerializer(entry).data)

    @extend_schema(request=None, responses={204: None})
    def delete(
        self,
        request,
        organization_id,
        league_id,
        season_id,
        season_team_id,
        roster_entry_id,
    ):
        organization, _, _, season_team = self.get_season_team(
            request,
            organization_id,
            league_id,
            season_id,
            season_team_id,
        )
        self.require_manager(request, organization)
        entry = get_object_or_404(season_team.roster_entries, pk=roster_entry_id)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FixtureListGenerateView(CompetitionScopedAPIView):
    @extend_schema(responses=FixtureSerializer(many=True))
    def get(self, request, organization_id, league_id, season_id):
        _, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        fixtures = season.fixtures.select_related("home_team", "away_team").all()
        round_number = request.query_params.get("round")
        if round_number:
            try:
                fixtures = fixtures.filter(round_number=int(round_number))
            except ValueError as exc:
                raise ValidationError({"round": "Round must be an integer."}) from exc
        team_id = request.query_params.get("team")
        if team_id:
            try:
                fixtures = fixtures.filter(
                    Q(home_team_id=int(team_id)) | Q(away_team_id=int(team_id))
                )
            except ValueError as exc:
                raise ValidationError({"team": "Team must be an integer ID."}) from exc
        fixtures = apply_query_options(
            fixtures,
            request,
            ordering_fields=("round_number", "leg", "scheduled_at"),
            default_ordering=("round_number", "leg", "id"),
        )
        return response_for_queryset(fixtures, request, FixtureSerializer, view=self)

    @extend_schema(
        request=FixtureGenerationSerializer,
        responses={201: FixtureSerializer(many=True)},
    )
    def post(self, request, organization_id, league_id, season_id):
        organization, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        self.require_manager(request, organization)
        serializer = FixtureGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            fixtures = RoundRobinFixtureGenerator.generate_for_season(
                season,
                double_round_robin=serializer.validated_data["double_round_robin"],
            )
        except FixturesAlreadyGenerated as exc:
            return Response(
                {"detail": str(exc), "code": "conflict"},
                status=status.HTTP_409_CONFLICT,
            )
        except FixtureGenerationError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        return Response(
            FixtureSerializer(fixtures, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class SeasonStandingsView(CompetitionScopedAPIView):
    @extend_schema(responses=StandingsSerializer(many=True))
    def get(self, request, organization_id, league_id, season_id):
        _, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        standings = get_season_standings(season)
        return response_for_queryset(
            standings,
            request,
            StandingsSerializer,
            view=self,
        )


class SeasonPlayerStatisticsView(CompetitionScopedAPIView):
    @extend_schema(responses=PlayerStatisticsSerializer(many=True))
    def get(self, request, organization_id, league_id, season_id):
        organization, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        players = get_season_player_statistics(season, organization)
        return response_for_queryset(
            players,
            request,
            PlayerStatisticsSerializer,
            view=self,
        )


class SeasonTopScorersView(CompetitionScopedAPIView):
    @extend_schema(responses=PlayerStatisticsSerializer(many=True))
    def get(self, request, organization_id, league_id, season_id):
        organization, _, season = self.get_season(
            request,
            organization_id,
            league_id,
            season_id,
        )
        players = get_season_player_statistics(season, organization)[:10]
        return response_for_queryset(
            players,
            request,
            PlayerStatisticsSerializer,
            view=self,
        )

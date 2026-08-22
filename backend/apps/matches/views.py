from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.competitions.models import Season
from apps.competitions.permissions import IsCompetitionManager
from apps.organizations.models import Organization
from apps.organizations.permissions import IsOrganizationMember

from .models import Match
from .serializers import MatchCreateSerializer, MatchEventSerializer, MatchSerializer
from .services import (
    MatchEventError,
    MatchLifecycleError,
    add_match_event,
    cancel_match,
    create_match_from_fixture,
    finish_match,
    postpone_match,
    start_match,
)


class MatchAccessMixin:
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_organization(self, request, organization_id):
        organization = get_object_or_404(
            Organization.objects.filter(memberships__user=request.user),
            pk=organization_id,
        )
        self.check_object_permissions(request, organization)
        return organization

    def require_manager(self, request, organization):
        if not IsCompetitionManager().has_object_permission(request, self, organization):
            raise PermissionDenied(IsCompetitionManager.message)

    def get_season(self, request, organization_id, league_id, season_id):
        organization = self.get_organization(request, organization_id)
        season = get_object_or_404(
            Season.objects.filter(league__organization=organization, league_id=league_id),
            pk=season_id,
        )
        return organization, season

    def get_match(self, request, organization_id, league_id, season_id, match_id):
        organization, season = self.get_season(request, organization_id, league_id, season_id)
        match = get_object_or_404(
            Match.objects.select_related("fixture__home_team", "fixture__away_team"),
            fixture__season=season,
            pk=match_id,
        )
        return organization, season, match


class MatchListCreateView(MatchAccessMixin, APIView):
    @extend_schema(responses=MatchSerializer(many=True))
    def get(self, request, organization_id, league_id, season_id):
        _, season = self.get_season(request, organization_id, league_id, season_id)
        matches = Match.objects.filter(fixture__season=season).select_related(
            "fixture__home_team", "fixture__away_team"
        )
        return Response(MatchSerializer(matches, many=True).data)

    @extend_schema(request=MatchCreateSerializer, responses={201: MatchSerializer})
    def post(self, request, organization_id, league_id, season_id):
        organization, season = self.get_season(request, organization_id, league_id, season_id)
        self.require_manager(request, organization)
        serializer = MatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fixture = serializer.validated_data["fixture_id"]
        if fixture.season_id != season.pk:
            raise ValidationError({"fixture_id": "Fixture does not belong to this season."})
        try:
            match = create_match_from_fixture(fixture)
        except MatchLifecycleError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        match = Match.objects.select_related("fixture__home_team", "fixture__away_team").get(pk=match.pk)
        return Response(MatchSerializer(match).data, status=status.HTTP_201_CREATED)


class MatchDetailView(MatchAccessMixin, APIView):
    @extend_schema(responses=MatchSerializer)
    def get(self, request, organization_id, league_id, season_id, match_id):
        _, _, match = self.get_match(request, organization_id, league_id, season_id, match_id)
        return Response(MatchSerializer(match).data)


class MatchTransitionView(MatchAccessMixin, APIView):
    transition = None

    @extend_schema(request=None, responses=MatchSerializer)
    def post(self, request, organization_id, league_id, season_id, match_id):
        organization, _, match = self.get_match(request, organization_id, league_id, season_id, match_id)
        self.require_manager(request, organization)
        try:
            updated = self.transition(match)
        except MatchLifecycleError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        updated = Match.objects.select_related("fixture__home_team", "fixture__away_team").get(pk=updated.pk)
        return Response(MatchSerializer(updated).data)


class StartMatchView(MatchTransitionView):
    transition = staticmethod(start_match)


class FinishMatchView(MatchTransitionView):
    transition = staticmethod(finish_match)


class CancelMatchView(MatchTransitionView):
    transition = staticmethod(cancel_match)


class PostponeMatchView(MatchTransitionView):
    transition = staticmethod(postpone_match)


class MatchEventListCreateView(MatchAccessMixin, APIView):
    @extend_schema(responses=MatchEventSerializer(many=True))
    def get(self, request, organization_id, league_id, season_id, match_id):
        _, _, match = self.get_match(request, organization_id, league_id, season_id, match_id)
        events = match.events.select_related("team", "player", "related_player")
        return Response(MatchEventSerializer(events, many=True).data)

    @extend_schema(request=MatchEventSerializer, responses={201: MatchEventSerializer})
    def post(self, request, organization_id, league_id, season_id, match_id):
        organization, _, match = self.get_match(request, organization_id, league_id, season_id, match_id)
        self.require_manager(request, organization)
        serializer = MatchEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            event = add_match_event(match, **serializer.validated_data)
        except MatchEventError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(
            MatchEventSerializer(event).data,
            status=status.HTTP_201_CREATED,
        )

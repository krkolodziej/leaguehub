import pytest
from django.core.management import call_command

from apps.competitions.models import Fixture, League, Player, RosterEntry, Season, SeasonTeam, Team
from apps.matches.models import Match
from apps.organizations.models import Organization, OrganizationMembership


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    counts = tuple(model.objects.count() for model in (Organization, OrganizationMembership, League, Season, Team, SeasonTeam, Player, RosterEntry, Fixture, Match))
    call_command("seed_demo")
    assert counts == tuple(model.objects.count() for model in (Organization, OrganizationMembership, League, Season, Team, SeasonTeam, Player, RosterEntry, Fixture, Match))
    assert Match.objects.filter(status=Match.Status.FINISHED).count() == 6

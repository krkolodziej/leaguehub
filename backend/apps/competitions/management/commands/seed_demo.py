import os
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.competitions.models import Fixture, League, Player, RosterEntry, Season, SeasonTeam, Team
from apps.matches.models import Match
from apps.organizations.models import Organization, OrganizationMembership


class Command(BaseCommand):
    help = "Create an idempotent LeagueHub demonstration dataset."

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.environ.get("DEMO_USER_PASSWORD", "demo-only-change-me")
        user, created = User.objects.get_or_create(
            email="demo@example.com",
            defaults={"first_name": "Demo", "last_name": "Manager", "is_active": True},
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])

        organization, _ = Organization.objects.get_or_create(
            slug="demo-league",
            defaults={"name": "Demo League", "created_by": user},
        )
        OrganizationMembership.objects.get_or_create(
            organization=organization,
            user=user,
            defaults={"role": OrganizationMembership.Role.OWNER},
        )
        league, _ = League.objects.get_or_create(
            organization=organization,
            slug="demo-division",
            defaults={"name": "Demo Division", "description": "Seeded demonstration competition."},
        )
        season, _ = Season.objects.get_or_create(
            league=league,
            name="2026 Demo",
            defaults={"start_date": date(2026, 1, 1)},
        )

        teams = []
        for index, name in enumerate(("North Stars", "River Plate", "City Rovers", "United FC"), start=1):
            team, _ = Team.objects.get_or_create(
                organization=organization,
                slug=f"demo-team-{index}",
                defaults={"name": name},
            )
            season_team, _ = SeasonTeam.objects.get_or_create(season=season, team=team)
            player, _ = Player.objects.get_or_create(
                organization=organization,
                first_name="Demo",
                last_name=f"Player {index}",
            )
            RosterEntry.objects.get_or_create(
                season_team=season_team,
                player=player,
                defaults={"shirt_number": index, "position": "Midfielder", "is_captain": index == 1},
            )
            teams.append((team, player))

        now = timezone.now()
        scores = ((2, 1), (1, 0), (2, 2), (0, 1), (3, 1), (1, 2))
        fixture_index = 0
        for home_index in range(len(teams)):
            for away_index in range(home_index + 1, len(teams)):
                home, _ = teams[home_index]
                away, _ = teams[away_index]
                fixture, _ = Fixture.objects.get_or_create(
                    season=season,
                    home_team=home,
                    away_team=away,
                    defaults={
                        "round_number": fixture_index // 2 + 1,
                        "leg": 1,
                        "scheduled_at": now - timedelta(days=fixture_index + 1),
                    },
                )
                home_score, away_score = scores[fixture_index]
                Match.objects.update_or_create(
                    fixture=fixture,
                    defaults={
                        "status": Match.Status.FINISHED,
                        "home_score": home_score,
                        "away_score": away_score,
                        "started_at": fixture.scheduled_at,
                        "finished_at": fixture.scheduled_at + timedelta(hours=2),
                    },
                )
                fixture_index += 1

        self.stdout.write(self.style.SUCCESS("Demo data ready: demo@example.com / configured DEMO_USER_PASSWORD"))

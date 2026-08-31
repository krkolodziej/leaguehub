"""Build a realistic, self-consistent LeagueHub dataset for demonstrations."""

import math
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.competitions.models import (
    Fixture,
    League,
    Player,
    RosterEntry,
    Season,
    SeasonTeam,
    Team,
)
from apps.competitions.services.fixture_generator import RoundRobinFixtureGenerator
from apps.matches.models import Match, MatchEvent
from apps.matches.services import (
    add_match_event,
    cancel_match,
    create_match_from_fixture,
    finish_match,
    postpone_match,
    start_match,
)
from apps.organizations.models import Organization, OrganizationMembership

RANDOM_SEED = 42

ORGANIZATION_NAME = "Podkarpacka Liga Amatorska"
ORGANIZATION_SLUG = "podkarpacka-liga-amatorska"
LEAGUE_NAME = "Liga Okręgowa"
LEAGUE_SLUG = "liga-okregowa"
LEAGUE_DESCRIPTION = (
    "Regional amateur division played across Podkarpacie over autumn and spring."
)

DEMO_PASSWORD = "demo1234"

# An earlier version of this command seeded a different organization and user.
# Databases that ran it keep both sets side by side, and signing in with the old
# account shows an all-but-empty league, so --flush clears those records too.
LEGACY_ORGANIZATION_SLUGS = ("demo-league",)
LEGACY_USER_EMAILS = ("demo@example.com",)


@dataclass(frozen=True)
class UserSpec:
    email: str
    first_name: str
    last_name: str
    role: str


DEMO_USERS = (
    UserSpec(
        "demo@leaguehub.app",
        "Marek",
        "Zawadzki",
        OrganizationMembership.Role.OWNER,
    ),
    UserSpec(
        "admin@leaguehub.app",
        "Iwona",
        "Bartosik",
        OrganizationMembership.Role.ADMIN,
    ),
    UserSpec(
        "member@leaguehub.app",
        "Tadeusz",
        "Rybak",
        OrganizationMembership.Role.MEMBER,
    ),
)


@dataclass(frozen=True)
class TeamSpec:
    name: str
    slug: str
    strength: float


# Hidden strengths shape the final table: a clear top three, a mid-table
# cluster, and two clubs adrift at the bottom.
TEAM_SPECS = (
    TeamSpec("Stal Łańcut", "stal-lancut", 1.45),
    TeamSpec("Karpaty Krosno", "karpaty-krosno", 1.36),
    TeamSpec("Resovia II", "resovia-ii", 1.28),
    TeamSpec("Polonia Przemyśl", "polonia-przemysl", 1.12),
    TeamSpec("Sokół Sieniawa", "sokol-sieniawa", 1.06),
    TeamSpec("Czarni Jasło", "czarni-jaslo", 1.02),
    TeamSpec("Wisłoka Dębica", "wisloka-debica", 1.00),
    TeamSpec("Orzeł Przeworsk", "orzel-przeworsk", 0.97),
    TeamSpec("Izolator Boguchwała", "izolator-boguchwala", 0.93),
    TeamSpec("Błękitni Ropczyce", "blekitni-ropczyce", 0.88),
    TeamSpec("Piast Tuczempy", "piast-tuczempy", 0.79),
    TeamSpec("Sanovia Lesko", "sanovia-lesko", 0.72),
)

FIRST_NAMES = (
    "Jakub", "Kamil", "Mateusz", "Bartosz", "Piotr", "Tomasz", "Grzegorz",
    "Łukasz", "Michał", "Damian", "Rafał", "Krzysztof", "Adrian", "Sebastian",
    "Paweł", "Marcin", "Dawid", "Konrad", "Patryk", "Wojciech", "Maciej",
    "Szymon", "Filip", "Arkadiusz", "Norbert", "Dominik", "Przemysław",
    "Karol", "Hubert", "Oskar",
)

LAST_NAMES = (
    "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński",
    "Lewandowski", "Zieliński", "Szymański", "Woźniak", "Dąbrowski",
    "Kozłowski", "Jankowski", "Mazur", "Kwiatkowski", "Krawczyk", "Piotrowski",
    "Grabowski", "Nowicki", "Pawłowski", "Michalski", "Adamczyk", "Dudek",
    "Zając", "Wieczorek", "Jabłoński", "Król", "Majewski", "Olszewski",
    "Jaworski", "Wróbel", "Malinowski", "Pawlak", "Witkowski", "Walczak",
    "Stępień", "Górski", "Rutkowski", "Michalak", "Sikora", "Ostrowski",
    "Baran", "Duda", "Szewczyk", "Tomaszewski", "Pietrzak", "Marciniak",
    "Wróblewski",
)

GOALKEEPER = "Goalkeeper"
DEFENDER = "Defender"
MIDFIELDER = "Midfielder"
FORWARD = "Forward"

# Squad shapes keyed by squad size: goalkeepers, defenders, midfielders, forwards.
SQUAD_SHAPES = {
    16: (2, 5, 6, 3),
    17: (2, 6, 6, 3),
    18: (2, 6, 7, 3),
}

GOAL_WEIGHTS = {
    GOALKEEPER: 0.02,
    DEFENDER: 0.5,
    MIDFIELDER: 1.6,
    FORWARD: 4.0,
}
CARD_WEIGHTS = {
    GOALKEEPER: 0.3,
    DEFENDER: 1.8,
    MIDFIELDER: 1.6,
    FORWARD: 1.0,
}
# Each squad gets one prolific striker and one attacking midfielder so the
# top-scorer chart has recognisable names instead of uniform noise.
TALISMAN_MULTIPLIERS = {FORWARD: 4.0, MIDFIELDER: 2.5}

BASE_GOALS = 1.28
HOME_ADVANTAGE = 1.20
# Damping the strength ratio keeps mismatches from turning into routs and
# leaves roughly a quarter of the fixtures drawn, as in a real division.
STRENGTH_DAMPING = 0.55
MIN_EXPECTED_GOALS = 0.35
MAX_EXPECTED_GOALS = 3.0
MAX_GOALS = 6
EXPECTED_YELLOW_CARDS = 3.1
MAX_YELLOW_CARDS = 7
RED_CARD_PROBABILITY = 0.055

ROUND_GAP_DAYS = 14
PLAYED_ROUNDS = 13
DISRUPTED_STATUSES = (
    Match.Status.CANCELLED,
    Match.Status.POSTPONED,
    Match.Status.POSTPONED,
)
# Saturday and Sunday kickoff slots as (day offset, hour) pairs, one per match.
KICKOFF_SLOTS = ((0, 11), (0, 13), (0, 15), (0, 17), (1, 12), (1, 16))
SEASON_PADDING_DAYS = 10
LIVE_MATCH_MINUTES_PLAYED = 63
FULL_TIME_MINUTES = 105


def _poisson(rng: random.Random, mean: float) -> int:
    """Draw a Poisson sample with the Knuth algorithm using the seeded generator."""
    limit = math.exp(-mean)
    product = rng.random()
    goals = 0
    while product > limit and goals < MAX_GOALS:
        product *= rng.random()
        goals += 1
    return goals


def _expected_goals(attack: float, defence: float, *, at_home: bool) -> float:
    expected = BASE_GOALS * (attack / defence) ** STRENGTH_DAMPING
    if at_home:
        expected *= HOME_ADVANTAGE
    return min(max(expected, MIN_EXPECTED_GOALS), MAX_EXPECTED_GOALS)


def _next_saturday(day: date) -> date:
    return day + timedelta(days=(5 - day.weekday()) % 7)


def _first_round_date() -> date:
    return _next_saturday(
        timezone.localdate() - timedelta(days=PLAYED_ROUNDS * ROUND_GAP_DAYS)
    )


def _season_label(start: date, end: date) -> str:
    if start.year == end.year:
        return str(start.year)
    return f"{start.year}/{end.year % 100:02d}"


def _aware(day: date, hour: int) -> datetime:
    return timezone.make_aware(datetime.combine(day, time(hour=hour)))


class Command(BaseCommand):
    help = "Create a realistic, idempotent LeagueHub demonstration dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Remove previously seeded demonstration data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()
        elif Organization.objects.filter(slug=ORGANIZATION_SLUG).exists():
            self.stdout.write(
                self.style.WARNING(
                    "Demonstration data is already present; nothing to do. "
                    "Re-run with --flush to rebuild it from scratch."
                )
            )
            return

        rng = random.Random(RANDOM_SEED)
        owner, organization = self._create_organization()
        league, season = self._create_league(organization)
        squads = self._create_teams_and_squads(rng, organization, season)
        rounds = self._generate_fixtures(season)
        self._play_season(rng, rounds, squads)
        self._report(organization, owner, league, season)

    def _flush(self):
        for slug in (ORGANIZATION_SLUG, *LEGACY_ORGANIZATION_SLUGS):
            organization = Organization.objects.filter(slug=slug).first()
            if organization is None:
                continue
            # Matches go first so their events release the PROTECT references
            # they hold on teams and players.
            Match.objects.filter(
                fixture__season__league__organization=organization
            ).delete()
            organization.delete()
        # Notifications cascade with their user.
        emails = [spec.email for spec in DEMO_USERS] + list(LEGACY_USER_EMAILS)
        User.objects.filter(email__in=emails).delete()

    def _create_organization(self):
        users = [
            User.objects.create_user(
                spec.email,
                DEMO_PASSWORD,
                first_name=spec.first_name,
                last_name=spec.last_name,
            )
            for spec in DEMO_USERS
        ]
        owner = users[0]
        organization = Organization.objects.create(
            name=ORGANIZATION_NAME,
            slug=ORGANIZATION_SLUG,
            created_by=owner,
        )
        for spec, user in zip(DEMO_USERS, users, strict=True):
            OrganizationMembership.objects.create(
                organization=organization,
                user=user,
                role=spec.role,
            )
        return owner, organization

    def _create_league(self, organization):
        league = League.objects.create(
            organization=organization,
            name=LEAGUE_NAME,
            slug=LEAGUE_SLUG,
            description=LEAGUE_DESCRIPTION,
        )
        first_round = _first_round_date()
        round_count = 2 * (len(TEAM_SPECS) - 1)
        last_round = first_round + timedelta(days=(round_count - 1) * ROUND_GAP_DAYS)
        start_date = first_round - timedelta(days=SEASON_PADDING_DAYS)
        end_date = last_round + timedelta(days=SEASON_PADDING_DAYS + 1)
        season = Season.objects.create(
            league=league,
            name=_season_label(start_date, end_date),
            start_date=start_date,
            end_date=end_date,
        )
        return league, season

    def _create_teams_and_squads(self, rng, organization, season):
        """Create every club with a full squad and return the squads by team ID."""
        used_names: set[tuple[str, str]] = set()
        squads = {}
        for spec in TEAM_SPECS:
            team = Team.objects.create(
                organization=organization,
                name=spec.name,
                slug=spec.slug,
            )
            season_team = SeasonTeam.objects.create(season=season, team=team)
            squads[team.pk] = {
                "spec": spec,
                "team": team,
                "squad": self._create_squad(
                    rng, organization, season_team, used_names
                ),
            }
        return squads

    def _create_squad(self, rng, organization, season_team, used_names):
        squad_size = rng.choice(sorted(SQUAD_SHAPES))
        keepers, defenders, midfielders, forwards = SQUAD_SHAPES[squad_size]
        positions = (
            [GOALKEEPER] * keepers
            + [DEFENDER] * defenders
            + [MIDFIELDER] * midfielders
            + [FORWARD] * forwards
        )
        captain_index = rng.randrange(keepers, len(positions) - forwards)
        talisman_awarded = {FORWARD: False, MIDFIELDER: False}

        squad = []
        for index, position in enumerate(positions):
            first_name, last_name = self._unique_name(rng, used_names)
            player = Player.objects.create(
                organization=organization,
                first_name=first_name,
                last_name=last_name,
            )
            RosterEntry.objects.create(
                season_team=season_team,
                player=player,
                shirt_number=index + 1,
                position=position,
                is_captain=index == captain_index,
            )
            goal_weight = GOAL_WEIGHTS[position]
            if position in talisman_awarded and not talisman_awarded[position]:
                goal_weight *= TALISMAN_MULTIPLIERS[position]
                talisman_awarded[position] = True
            squad.append(
                {
                    "player": player,
                    "goal_weight": goal_weight,
                    "card_weight": CARD_WEIGHTS[position],
                }
            )
        return squad

    def _unique_name(self, rng, used_names):
        while True:
            candidate = (rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES))
            if candidate not in used_names:
                used_names.add(candidate)
                return candidate

    def _generate_fixtures(self, season):
        """Delegate the calendar to the round-robin generator, then date it."""
        fixtures = RoundRobinFixtureGenerator.generate_for_season(
            season, double_round_robin=True
        )
        rounds: dict[int, list[Fixture]] = {}
        for fixture in fixtures:
            rounds.setdefault(fixture.round_number, []).append(fixture)

        first_round = _first_round_date()
        for round_number, round_fixtures in rounds.items():
            match_day = first_round + timedelta(
                days=(round_number - 1) * ROUND_GAP_DAYS
            )
            for fixture, (day_offset, hour) in zip(
                round_fixtures, KICKOFF_SLOTS, strict=True
            ):
                fixture.scheduled_at = _aware(
                    match_day + timedelta(days=day_offset), hour
                )
        Fixture.objects.bulk_update(fixtures, ["scheduled_at"])
        return rounds

    def _play_season(self, rng, rounds, squads):
        played = [
            fixture
            for round_number in sorted(rounds)
            if round_number <= PLAYED_ROUNDS
            for fixture in rounds[round_number]
        ]
        disrupted = {
            fixture.pk: status
            for fixture, status in zip(
                rng.sample(played, len(DISRUPTED_STATUSES)),
                DISRUPTED_STATUSES,
                strict=True,
            )
        }
        live_fixture = rounds[PLAYED_ROUNDS + 1][0]

        finished = []
        for round_number in sorted(rounds):
            for fixture in rounds[round_number]:
                match = create_match_from_fixture(fixture)
                if fixture.pk in disrupted:
                    self._disrupt(match, disrupted[fixture.pk])
                elif fixture.pk == live_fixture.pk:
                    self._play_live(rng, match, fixture, squads)
                elif round_number <= PLAYED_ROUNDS:
                    finished.append(self._play_finished(rng, match, fixture, squads))
        Match.objects.bulk_update(finished, ["started_at", "finished_at"])

    def _disrupt(self, match, status):
        if status == Match.Status.CANCELLED:
            cancel_match(match)
        else:
            postpone_match(match)

    def _play_finished(self, rng, match, fixture, squads):
        """Replay a match event by event so the score derives from its goals."""
        home = squads[fixture.home_team_id]
        away = squads[fixture.away_team_id]
        home_goals = _poisson(
            rng,
            _expected_goals(home["spec"].strength, away["spec"].strength, at_home=True),
        )
        away_goals = _poisson(
            rng,
            _expected_goals(away["spec"].strength, home["spec"].strength, at_home=False),
        )

        match = start_match(match)
        for event in self._build_events(rng, home, away, home_goals, away_goals):
            add_match_event(match, **event)
        match = finish_match(match)

        match.started_at = fixture.scheduled_at
        match.finished_at = fixture.scheduled_at + timedelta(minutes=FULL_TIME_MINUTES)
        return match

    def _play_live(self, rng, match, fixture, squads):
        """One fixture is brought forward to today and left in progress."""
        home = squads[fixture.home_team_id]
        away = squads[fixture.away_team_id]
        kickoff = timezone.now() - timedelta(minutes=LIVE_MATCH_MINUTES_PLAYED)
        Fixture.objects.filter(pk=fixture.pk).update(scheduled_at=kickoff)

        match = start_match(match)
        events = [
            self._goal(rng, home, minute=rng.randint(5, 30)),
            self._goal(rng, away, minute=rng.randint(31, 50)),
            self._card(
                rng,
                away,
                MatchEvent.EventType.YELLOW_CARD,
                minute=rng.randint(51, LIVE_MATCH_MINUTES_PLAYED - 3),
            ),
        ]
        for event in sorted(events, key=lambda event: event["minute"]):
            add_match_event(match, **event)
        Match.objects.filter(pk=match.pk).update(started_at=kickoff)

    def _build_events(self, rng, home, away, home_goals, away_goals):
        events = []
        for side, goals in ((home, home_goals), (away, away_goals)):
            for _ in range(goals):
                events.append(self._goal(rng, side, minute=rng.randint(2, 90)))

        for _ in range(min(_poisson(rng, EXPECTED_YELLOW_CARDS), MAX_YELLOW_CARDS)):
            events.append(
                self._card(
                    rng,
                    rng.choice((home, away)),
                    MatchEvent.EventType.YELLOW_CARD,
                    minute=rng.randint(10, 90),
                )
            )
        if rng.random() < RED_CARD_PROBABILITY:
            events.append(
                self._card(
                    rng,
                    rng.choice((home, away)),
                    MatchEvent.EventType.RED_CARD,
                    minute=rng.randint(35, 90),
                )
            )
        return sorted(events, key=lambda event: event["minute"])

    def _goal(self, rng, side, *, minute):
        return {
            "event_type": MatchEvent.EventType.GOAL,
            "minute": minute,
            "team": side["team"],
            "player": self._pick(rng, side, "goal_weight"),
        }

    def _card(self, rng, side, event_type, *, minute):
        return {
            "event_type": event_type,
            "minute": minute,
            "team": side["team"],
            "player": self._pick(rng, side, "card_weight"),
        }

    def _pick(self, rng, side, weight_key):
        squad = side["squad"]
        return rng.choices(
            [member["player"] for member in squad],
            weights=[member[weight_key] for member in squad],
        )[0]

    def _report(self, organization, owner, league, season):
        matches = Match.objects.filter(
            fixture__season__league__organization=organization
        )
        counts = (
            ("Teams", SeasonTeam.objects.filter(season=season).count()),
            ("Players", Player.objects.filter(organization=organization).count()),
            ("Fixtures", Fixture.objects.filter(season=season).count()),
            ("Finished matches", matches.filter(status=Match.Status.FINISHED).count()),
            ("Live matches", matches.filter(status=Match.Status.LIVE).count()),
            (
                "Scheduled matches",
                matches.filter(status=Match.Status.SCHEDULED).count(),
            ),
            (
                "Cancelled or postponed",
                matches.filter(
                    status__in=(Match.Status.CANCELLED, Match.Status.POSTPONED)
                ).count(),
            ),
            ("Match events", MatchEvent.objects.filter(match__in=matches).count()),
        )

        self.stdout.write(
            self.style.SUCCESS(f"{organization.name} - {league.name} {season.name}")
        )
        self.stdout.write(f"  Season runs {season.start_date} to {season.end_date}")
        self.stdout.write(f"  Owned by {owner.get_full_name()}")
        for label, value in counts:
            self.stdout.write(f"  {label + ':':<24}{value}")
        self.stdout.write("")
        self.stdout.write("Sign in with any of these accounts:")
        for spec in DEMO_USERS:
            self.stdout.write(f"  {spec.email:<24}{DEMO_PASSWORD:<12}{spec.role}")

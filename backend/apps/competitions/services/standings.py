from django.db.models import Count, F, Q, Sum

from apps.matches.models import Match


def _empty_record(team_id, team_name):
    return {
        "team_id": team_id,
        "team_name": team_name,
        "mp": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0,
        "pts": 0,
    }


def _apply_side(record, row, *, home):
    prefix = "home" if home else "away"
    record["mp"] += row["mp"]
    record["wins"] += row[f"{prefix}_wins"]
    record["draws"] += row[f"{prefix}_draws"]
    record["losses"] += row[f"{prefix}_losses"]
    record["gf"] += row[f"{prefix}_gf"] or 0
    record["ga"] += row[f"{prefix}_ga"] or 0


def get_season_standings(season):
    """Return derived standings for a season without persisting duplicate data.

    Only finished matches count. Tie-breakers are points, goal difference,
    goals for, team name, and team ID, in that order.
    """
    records = {
        season_team.team_id: _empty_record(season_team.team_id, season_team.team.name)
        for season_team in season.season_teams.select_related("team")
    }
    if not records:
        return []

    finished = Match.objects.filter(
        fixture__season=season,
        status=Match.Status.FINISHED,
    )
    home_rows = finished.values("fixture__home_team_id").annotate(
        mp=Count("id"),
        home_wins=Count("id", filter=Q(home_score__gt=F("away_score"))),
        home_draws=Count("id", filter=Q(home_score=F("away_score"))),
        home_losses=Count("id", filter=Q(home_score__lt=F("away_score"))),
        home_gf=Sum("home_score"),
        home_ga=Sum("away_score"),
    )
    away_rows = finished.values("fixture__away_team_id").annotate(
        mp=Count("id"),
        away_wins=Count("id", filter=Q(away_score__gt=F("home_score"))),
        away_draws=Count("id", filter=Q(away_score=F("home_score"))),
        away_losses=Count("id", filter=Q(away_score__lt=F("home_score"))),
        away_gf=Sum("away_score"),
        away_ga=Sum("home_score"),
    )

    for row in home_rows:
        record = records.get(row["fixture__home_team_id"])
        if record:
            _apply_side(
                record,
                {
                    **row,
                    "home_wins": row["home_wins"],
                    "home_draws": row["home_draws"],
                    "home_losses": row["home_losses"],
                    "home_gf": row["home_gf"],
                    "home_ga": row["home_ga"],
                },
                home=True,
            )
    for row in away_rows:
        record = records.get(row["fixture__away_team_id"])
        if record:
            _apply_side(
                record,
                {
                    **row,
                    "away_wins": row["away_wins"],
                    "away_draws": row["away_draws"],
                    "away_losses": row["away_losses"],
                    "away_gf": row["away_gf"],
                    "away_ga": row["away_ga"],
                },
                home=False,
            )

    for record in records.values():
        record["gd"] = record["gf"] - record["ga"]
        record["pts"] = 3 * record["wins"] + record["draws"]

    return sorted(
        records.values(),
        key=lambda record: (
            -record["pts"],
            -record["gd"],
            -record["gf"],
            record["team_name"].casefold(),
            record["team_id"],
        ),
    )

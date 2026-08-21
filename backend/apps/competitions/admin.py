from django.contrib import admin

from .models import League, Player, RosterEntry, Season, SeasonTeam, Team


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "slug", "created_at")
    list_filter = ("organization",)
    search_fields = ("name", "slug", "organization__name")
    autocomplete_fields = ("organization",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "league", "start_date", "end_date")
    list_filter = ("league",)
    search_fields = ("name", "league__name")
    autocomplete_fields = ("league",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "slug")
    list_filter = ("organization",)
    search_fields = ("name", "slug", "organization__name")
    autocomplete_fields = ("organization",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(SeasonTeam)
class SeasonTeamAdmin(admin.ModelAdmin):
    list_display = ("team", "season", "organization_name")
    list_filter = ("season__league",)
    search_fields = ("team__name", "season__name", "season__league__name")
    autocomplete_fields = ("season", "team")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Organization")
    def organization_name(self, obj):
        return obj.season.league.organization.name


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "organization", "date_of_birth")
    list_filter = ("organization",)
    search_fields = ("first_name", "last_name", "organization__name")
    autocomplete_fields = ("organization",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(RosterEntry)
class RosterEntryAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "season_team",
        "shirt_number",
        "position",
        "is_captain",
    )
    list_filter = ("is_captain", "position", "season_team__season__league")
    search_fields = (
        "player__first_name",
        "player__last_name",
        "season_team__team__name",
    )
    autocomplete_fields = ("season_team", "player")
    readonly_fields = ("created_at", "updated_at")

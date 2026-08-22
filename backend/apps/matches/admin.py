from django.contrib import admin

from .models import Match, MatchEvent


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("fixture", "status", "home_score", "away_score")
    list_filter = ("status",)


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ("match", "event_type", "minute", "team", "player")
    list_filter = ("event_type",)

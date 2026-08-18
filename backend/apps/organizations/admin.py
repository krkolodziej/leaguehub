from django.contrib import admin

from .models import Organization, OrganizationMembership


class OrganizationMembershipInline(admin.TabularInline):
    model = OrganizationMembership
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_by", "created_at")
    search_fields = ("name", "slug", "created_by__email")
    readonly_fields = ("created_at", "updated_at")
    inlines = (OrganizationMembershipInline,)


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ("organization", "user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("organization__name", "user__email")
    autocomplete_fields = ("organization", "user")
    readonly_fields = ("created_at", "updated_at")

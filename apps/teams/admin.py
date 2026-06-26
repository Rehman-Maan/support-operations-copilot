from django.contrib import admin

from .models import Team, TeamMembership


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_by", "created_at")
    list_filter = ("created_at",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug", "created_by__username", "created_by__email")


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("team", "user", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("team__name", "team__slug", "user__username", "user__email")

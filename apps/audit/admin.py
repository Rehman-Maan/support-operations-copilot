from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "team", "ticket", "actor_type", "actor_user", "created_at")
    list_filter = ("actor_type", "event_type", "team", "created_at")
    search_fields = ("event_type", "team__name", "ticket__subject", "actor_user__username")
    readonly_fields = ("created_at",)

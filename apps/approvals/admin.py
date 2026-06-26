from django.contrib import admin

from .models import ApprovalRequest


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ["ticket", "action_type", "status", "requested_by", "decided_by", "created_at"]
    list_filter = ["action_type", "status", "created_at", "decided_at"]
    search_fields = ["ticket__subject", "reason", "decision_note"]

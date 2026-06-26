from django.contrib import admin

from .models import Customer, Ticket, TicketMessage


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "team", "tier", "updated_at")
    list_filter = ("tier", "team", "created_at")
    search_fields = ("name", "email", "external_id", "team__name")


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    fields = ("sender_type", "sender_user", "customer", "channel", "body", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "team",
        "customer",
        "status",
        "priority",
        "assigned_to",
        "needs_escalation",
        "sla_due_at",
    )
    list_filter = ("status", "priority", "sla_risk_level", "needs_escalation", "team", "created_at")
    search_fields = ("subject", "customer__name", "customer__email", "assigned_to__username")
    inlines = [TicketMessageInline]


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ("ticket", "sender_type", "channel", "sender_user", "customer", "created_at")
    list_filter = ("sender_type", "channel", "created_at")
    search_fields = ("ticket__subject", "body", "sender_user__username", "customer__email")

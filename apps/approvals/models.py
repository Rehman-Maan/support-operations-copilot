from django.conf import settings
from django.db import models

from apps.copilot.models import CopilotSuggestion
from apps.tickets.models import Ticket


class ApprovalRequest(models.Model):
    class ActionType(models.TextChoices):
        REFUND = "refund", "Refund"
        CANCELLATION = "cancellation", "Cancellation"
        ACCOUNT_CLOSURE = "account_closure", "Account Closure"
        CREDIT_ADJUSTMENT = "credit_adjustment", "Credit Adjustment"
        DATA_EXPORT = "data_export", "Data Export"
        DATA_DELETION = "data_deletion", "Data Deletion"
        SUPPORT_LEAD_REVIEW = "support_lead_review", "Support Lead Review"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="approval_requests")
    suggestion = models.ForeignKey(
        CopilotSuggestion,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="approval_requests",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_approvals",
    )
    action_type = models.CharField(max_length=64, choices=ActionType.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    reason = models.TextField()
    proposed_payload = models.JSONField(default=dict, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="decided_approvals",
    )
    decision_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_action_type_display()} approval for {self.ticket}"

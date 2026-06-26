from django.conf import settings
from django.db import models

from apps.knowledge_base.models import KnowledgeChunk
from apps.tickets.models import Ticket


class CopilotSuggestion(models.Model):
    class SuggestionType(models.TextChoices):
        REPLY_DRAFT = "reply_draft", "Reply Draft"
        SUMMARY = "summary", "Summary"
        PRIORITY = "priority", "Priority"
        INTENT = "intent", "Intent"
        NEXT_ACTION = "next_action", "Next Action"
        MACRO = "macro", "Macro"

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        ACCEPTED = "accepted", "Accepted"
        EDITED = "edited", "Edited"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="suggestions")
    suggestion_type = models.CharField(max_length=32, choices=SuggestionType.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PROPOSED)
    content = models.TextField()
    internal_notes = models.TextField(blank=True)
    needs_approval = models.BooleanField(default=False)
    proposed_sensitive_action = models.CharField(max_length=128, blank=True)
    model_name = models.CharField(max_length=128)
    prompt_version = models.CharField(max_length=64)
    confidence_score = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        blank=True,
        null=True,
    )
    created_by_ai = models.BooleanField(default=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="accepted_copilot_suggestions",
    )
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="rejected_copilot_suggestions",
    )
    rejected_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_suggestion_type_display()} for {self.ticket}"


class RetrievedContext(models.Model):
    suggestion = models.ForeignKey(
        CopilotSuggestion,
        on_delete=models.CASCADE,
        related_name="retrieved_contexts",
    )
    knowledge_chunk = models.ForeignKey(
        KnowledgeChunk,
        on_delete=models.CASCADE,
        related_name="retrieved_contexts",
    )
    relevance_score = models.FloatField()
    content_snapshot = models.TextField()
    source_title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["relevance_score", "id"]

    def __str__(self) -> str:
        return f"{self.source_title} for {self.suggestion_id}"

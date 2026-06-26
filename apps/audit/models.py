from django.conf import settings
from django.db import models

from apps.teams.models import Team


class AuditEvent(models.Model):
    class ActorType(models.TextChoices):
        USER = "user", "User"
        AI = "ai", "AI"
        SYSTEM = "system", "System"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="audit_events")
    ticket = models.ForeignKey(
        "tickets.Ticket",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="audit_events",
    )
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    actor_type = models.CharField(max_length=32, choices=ActorType.choices)
    event_type = models.CharField(max_length=128)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.event_type} for {self.team}"

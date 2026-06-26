from django.conf import settings
from django.db import models

from apps.copilot.models import CopilotSuggestion


class SuggestionFeedback(models.Model):
    class Rating(models.IntegerChoices):
        POOR = 1, "Poor"
        FAIR = 2, "Fair"
        OK = 3, "OK"
        GOOD = 4, "Good"
        EXCELLENT = 5, "Excellent"

    class FailureTag(models.TextChoices):
        INACCURATE = "inaccurate", "Inaccurate"
        WRONG_POLICY = "wrong_policy", "Wrong Policy"
        MISSING_CONTEXT = "missing_context", "Missing Context"
        UNSAFE_ACTION = "unsafe_action", "Unsafe Action"
        TONE_ISSUE = "tone_issue", "Tone Issue"
        TOO_LONG = "too_long", "Too Long"
        TOO_SHORT = "too_short", "Too Short"
        HALLUCINATED = "hallucinated", "Hallucinated"
        PII_PROBLEM = "pii_problem", "PII Problem"

    suggestion = models.ForeignKey(
        CopilotSuggestion,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="suggestion_feedback",
    )
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    comment = models.TextField(blank=True)
    failure_tag = models.CharField(max_length=64, choices=FailureTag.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["suggestion", "user"],
                name="unique_feedback_per_suggestion_user",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_rating_display()} for suggestion {self.suggestion_id}"

from django.db import models

from apps.teams.models import Team


class EvaluationRun(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="evaluation_runs")
    name = models.CharField(max_length=255)
    dataset_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=128)
    classifier_f1 = models.FloatField(default=0.0)
    escalation_precision = models.FloatField(default=0.0)
    escalation_recall = models.FloatField(default=0.0)
    groundedness_score = models.FloatField(default=0.0)
    average_latency_ms = models.FloatField(default=0.0)
    case_count = models.PositiveIntegerField(default=0)
    failed_cases = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.dataset_name})"

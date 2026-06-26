from django.contrib import admin

from .models import EvaluationRun


@admin.register(EvaluationRun)
class EvaluationRunAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "team",
        "dataset_name",
        "classifier_f1",
        "escalation_precision",
        "escalation_recall",
        "groundedness_score",
        "created_at",
    ]
    list_filter = ["dataset_name", "created_at"]
    search_fields = ["name", "team__name", "dataset_name"]

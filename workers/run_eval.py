from apps.teams.models import Team
from config.celery import app
from services.evaluations.runner import run_support_case_evaluation


@app.task
def run_evaluation(dataset_name: str, team_id: int) -> dict:
    team = Team.objects.get(id=team_id)
    run = run_support_case_evaluation(dataset_name, team)
    return {
        "dataset_name": dataset_name,
        "status": "completed",
        "run_id": run.id,
        "classifier_f1": run.classifier_f1,
        "escalation_precision": run.escalation_precision,
        "escalation_recall": run.escalation_recall,
        "groundedness_score": run.groundedness_score,
    }

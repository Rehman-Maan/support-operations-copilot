import pytest
from django.contrib.auth import get_user_model

from apps.evaluations.models import EvaluationRun
from apps.teams.models import Team, TeamMembership
from services.evaluations.runner import run_support_case_evaluation
from workers.run_eval import run_evaluation


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def team(user):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=user)
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.SUPPORT_AGENT)
    return team


def test_run_support_case_evaluation_creates_metrics(team):
    run = run_support_case_evaluation("support_cases.yml", team)

    assert run.case_count == 4
    assert 0 <= run.classifier_f1 <= 1
    assert 0 <= run.escalation_precision <= 1
    assert 0 <= run.escalation_recall <= 1
    assert 0 <= run.groundedness_score <= 1


def test_run_evaluation_task_returns_summary(team):
    result = run_evaluation.run("support_cases.yml", team.id)

    assert result["status"] == "completed"
    assert EvaluationRun.objects.filter(id=result["run_id"]).exists()

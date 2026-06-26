import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.copilot.models import CopilotSuggestion
from apps.evaluations.models import EvaluationRun
from apps.feedback.models import SuggestionFeedback
from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket


@pytest.fixture
def agent(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def ticket(agent):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=agent)
    TeamMembership.objects.create(team=team, user=agent, role=TeamMembership.Role.SUPPORT_AGENT)
    customer = Customer.objects.create(team=team, name="Amina Khan", email="amina@example.com")
    return Ticket.objects.create(team=team, customer=customer, subject="Refund request")


@pytest.fixture
def suggestion(ticket):
    return CopilotSuggestion.objects.create(
        ticket=ticket,
        suggestion_type=CopilotSuggestion.SuggestionType.SUMMARY,
        content="Customer wants a refund.",
        model_name="local-heuristic",
        prompt_version="ticket-summary-v1",
    )


def test_submit_suggestion_feedback(client, agent, suggestion):
    client.force_login(agent)

    response = client.post(
        reverse("feedback:submit", args=[suggestion.id]),
        {
            "rating": SuggestionFeedback.Rating.GOOD,
            "failure_tag": "",
            "comment": "Useful summary.",
        },
    )

    assert response.status_code == 302
    assert SuggestionFeedback.objects.filter(suggestion=suggestion, user=agent).exists()


def test_evaluation_dashboard_and_queue_action(client, monkeypatch, agent, ticket):
    queued = []

    class FakeTask:
        @staticmethod
        def delay(dataset_name, team_id):
            queued.append((dataset_name, team_id))

    monkeypatch.setattr("apps.evaluations.views.run_evaluation", FakeTask)
    EvaluationRun.objects.create(
        team=ticket.team,
        name="Existing run",
        dataset_name="support_cases.yml",
        model_name="local-heuristic",
        classifier_f1=0.75,
        escalation_precision=0.8,
        escalation_recall=0.7,
        groundedness_score=0.9,
        case_count=4,
    )
    client.force_login(agent)

    dashboard_response = client.get(reverse("evaluations:dashboard"))
    queue_response = client.post(reverse("evaluations:run"))

    assert dashboard_response.status_code == 200
    assert b"Existing run" in dashboard_response.content
    assert queue_response.status_code == 302
    assert queued == [("support_cases.yml", ticket.team_id)]

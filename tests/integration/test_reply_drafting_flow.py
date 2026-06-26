import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.copilot.models import CopilotSuggestion
from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket, TicketMessage


@pytest.fixture
def agent(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def ticket(agent):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=agent)
    TeamMembership.objects.create(team=team, user=agent, role=TeamMembership.Role.SUPPORT_AGENT)
    customer = Customer.objects.create(team=team, name="Amina Khan", email="amina@example.com")
    ticket = Ticket.objects.create(team=team, customer=customer, subject="Refund request")
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="I want a refund for my order.",
    )
    return ticket


def test_draft_reply_action_queues_task(client, monkeypatch, agent, ticket):
    queued = []

    class FakeTask:
        @staticmethod
        def delay(ticket_id):
            queued.append(ticket_id)

    monkeypatch.setattr("apps.tickets.views.draft_reply", FakeTask)
    client.force_login(agent)

    response = client.post(reverse("tickets:draft_reply", args=[ticket.id]))

    assert response.status_code == 302
    assert queued == [ticket.id]


def test_accept_reply_suggestion_adds_agent_message(client, agent, ticket):
    suggestion = CopilotSuggestion.objects.create(
        ticket=ticket,
        suggestion_type=CopilotSuggestion.SuggestionType.REPLY_DRAFT,
        content="Thanks for reaching out. I will review this with the team.",
        model_name="local-heuristic",
        prompt_version="reply-draft-v1",
    )
    client.force_login(agent)

    response = client.post(
        reverse("tickets:accept_suggestion", args=[ticket.id, suggestion.id]),
        {"content": "Thanks for reaching out. I will review this with the team."},
    )
    suggestion.refresh_from_db()
    ticket.refresh_from_db()

    assert response.status_code == 302
    assert suggestion.status == CopilotSuggestion.Status.ACCEPTED
    assert ticket.status == Ticket.Status.PENDING_CUSTOMER
    assert ticket.messages.filter(sender_type=TicketMessage.SenderType.AGENT).exists()


def test_reject_reply_suggestion_marks_rejected(client, agent, ticket):
    suggestion = CopilotSuggestion.objects.create(
        ticket=ticket,
        suggestion_type=CopilotSuggestion.SuggestionType.REPLY_DRAFT,
        content="Draft text",
        model_name="local-heuristic",
        prompt_version="reply-draft-v1",
    )
    client.force_login(agent)

    response = client.post(reverse("tickets:reject_suggestion", args=[ticket.id, suggestion.id]))
    suggestion.refresh_from_db()

    assert response.status_code == 302
    assert suggestion.status == CopilotSuggestion.Status.REJECTED

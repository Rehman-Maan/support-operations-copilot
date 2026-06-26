import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.copilot.models import CopilotSuggestion
from apps.knowledge_base.models import Macro
from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket, TicketMessage
from services.summarization.summarizer import build_redacted_conversation, summarize_ticket
from workers.summarize_thread import summarize_thread


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def team(user):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=user)
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.SUPPORT_AGENT)
    return team


@pytest.fixture
def customer(team):
    return Customer.objects.create(team=team, name="Amina Khan", email="amina@example.com")


@pytest.fixture
def ticket(team, customer):
    ticket = Ticket.objects.create(
        team=team,
        customer=customer,
        subject="Package never arrived",
        intent=Ticket.Intent.REFUND_REQUEST,
        priority=Ticket.Priority.HIGH,
        needs_escalation=True,
    )
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="My order ORD-12345 never arrived. Email me at amina@example.com.",
    )
    return ticket


@pytest.fixture
def macro(team, user):
    return Macro.objects.create(
        team=team,
        name="Refund acknowledgement",
        intent=Ticket.Intent.REFUND_REQUEST,
        body="I will verify the order and refund policy before confirming next steps.",
        created_by=user,
    )


def test_build_redacted_conversation_updates_redacted_body(ticket):
    conversation, counts = build_redacted_conversation(ticket)
    message = ticket.messages.first()
    message.refresh_from_db()

    assert "amina@example.com" not in conversation
    assert counts["email"] == 1
    assert message.redacted_body


def test_summarize_ticket_creates_summary_next_action_macro_and_audit(
    settings,
    ticket,
    macro,
):
    settings.OPENAI_API_KEY = ""

    suggestions = summarize_ticket(ticket)

    assert suggestions["summary"].suggestion_type == CopilotSuggestion.SuggestionType.SUMMARY
    assert (
        suggestions["next_action"].suggestion_type
        == CopilotSuggestion.SuggestionType.NEXT_ACTION
    )
    assert suggestions["macro"].suggestion_type == CopilotSuggestion.SuggestionType.MACRO
    assert macro.body in suggestions["macro"].content
    assert AuditEvent.objects.filter(ticket=ticket, event_type="ticket_summarized").exists()


def test_summarize_thread_task_returns_created_suggestions(settings, ticket, macro):
    settings.OPENAI_API_KEY = ""

    result = summarize_thread.run(ticket.id)

    assert result["status"] == CopilotSuggestion.Status.PROPOSED
    assert result["summary_id"]
    assert result["next_action_id"]
    assert result["macro_suggestion_id"]

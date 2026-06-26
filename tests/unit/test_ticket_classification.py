import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket, TicketMessage
from services.ticket_classification.classifier import build_redacted_ticket_text, classify_ticket
from services.ticket_classification.parser import parse_classification
from workers.classify_ticket import classify_ticket as classify_ticket_task


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
    ticket = Ticket.objects.create(team=team, customer=customer, subject="Package never arrived")
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="My order ORD-12345 never arrived. Email me at amina@example.com. I want a refund.",
    )
    return ticket


def test_parse_classification_defaults_unknown_values():
    result = parse_classification(
        {
            "intent": "not_real",
            "priority": "urgent",
            "sla_risk_level": "also_fake",
            "sentiment": "frustrated",
            "needs_escalation": True,
            "reason": "Customer is upset.",
        },
        model_name="test-model",
    )

    assert result.intent == Ticket.Intent.OTHER
    assert result.priority == Ticket.Priority.URGENT
    assert result.sla_risk_level == Ticket.SlaRiskLevel.NONE


def test_build_redacted_ticket_text_updates_message_redacted_body(ticket):
    redacted_text, counts = build_redacted_ticket_text(ticket)
    message = ticket.messages.first()

    message.refresh_from_db()
    assert "amina@example.com" not in redacted_text
    assert "ORD-12345" not in redacted_text
    assert counts["email"] == 1
    assert message.redacted_body


def test_classify_ticket_updates_fields_and_audit_event(settings, ticket):
    settings.OPENAI_API_KEY = ""

    result = classify_ticket(ticket)
    ticket.refresh_from_db()

    assert result.intent == Ticket.Intent.REFUND_REQUEST
    assert ticket.intent == Ticket.Intent.REFUND_REQUEST
    assert ticket.priority == Ticket.Priority.HIGH
    assert ticket.sla_risk_level == Ticket.SlaRiskLevel.MEDIUM
    assert ticket.needs_escalation is True
    assert ticket.classified_at is not None
    assert AuditEvent.objects.filter(ticket=ticket, event_type="ticket_classified").exists()


def test_classify_ticket_task_returns_summary(settings, ticket):
    settings.OPENAI_API_KEY = ""

    result = classify_ticket_task.run(ticket.id)

    assert result["status"] == "classified"
    assert result["intent"] == Ticket.Intent.REFUND_REQUEST

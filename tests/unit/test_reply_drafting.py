import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.copilot.models import CopilotSuggestion
from apps.knowledge_base.models import KnowledgeChunk, KnowledgeDocument
from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket, TicketMessage
from services.embeddings.local import embed_text
from services.reply_drafting.drafter import build_retrieval_query, draft_reply
from workers.draft_reply import draft_reply as draft_reply_task


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
        subject="Refund for late package",
        intent=Ticket.Intent.REFUND_REQUEST,
        priority=Ticket.Priority.HIGH,
        needs_escalation=True,
    )
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="My order ORD-12345 never arrived. Please refund amina@example.com.",
    )
    return ticket


@pytest.fixture
def knowledge_chunk(team, user):
    document = KnowledgeDocument.objects.create(
        team=team,
        title="Refund Policy",
        uploaded_by=user,
        status=KnowledgeDocument.Status.READY,
    )
    return KnowledgeChunk.objects.create(
        team=team,
        document=document,
        chunk_index=0,
        content="Refunds require support lead approval and order verification.",
        embedding=embed_text("refund approval order verification"),
    )


def test_build_retrieval_query_uses_ticket_context(ticket):
    query = build_retrieval_query(ticket)

    assert "Refund for late package" in query
    assert Ticket.Intent.REFUND_REQUEST in query


def test_draft_reply_creates_suggestion_sources_and_audit_event(settings, ticket, knowledge_chunk):
    settings.OPENAI_API_KEY = ""

    suggestion = draft_reply(ticket)
    ticket.messages.first().refresh_from_db()

    assert suggestion.suggestion_type == CopilotSuggestion.SuggestionType.REPLY_DRAFT
    assert suggestion.status == CopilotSuggestion.Status.PROPOSED
    assert suggestion.needs_approval is True
    assert suggestion.retrieved_contexts.filter(knowledge_chunk=knowledge_chunk).exists()
    assert ticket.messages.first().redacted_body
    assert AuditEvent.objects.filter(ticket=ticket, event_type="reply_draft_created").exists()


def test_draft_reply_task_returns_summary(settings, ticket, knowledge_chunk):
    settings.OPENAI_API_KEY = ""

    result = draft_reply_task.run(ticket.id)

    assert result["status"] == CopilotSuggestion.Status.PROPOSED
    assert result["needs_approval"] is True

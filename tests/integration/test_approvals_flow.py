import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.approvals.models import ApprovalRequest
from apps.copilot.models import CopilotSuggestion
from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket, TicketMessage


@pytest.fixture
def agent(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def lead(db):
    return get_user_model().objects.create_user(username="lead", password="test-pass")


@pytest.fixture
def viewer(db):
    return get_user_model().objects.create_user(username="viewer", password="test-pass")


@pytest.fixture
def team(agent, lead, viewer):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=agent)
    TeamMembership.objects.create(team=team, user=agent, role=TeamMembership.Role.SUPPORT_AGENT)
    TeamMembership.objects.create(team=team, user=lead, role=TeamMembership.Role.SUPPORT_LEAD)
    TeamMembership.objects.create(team=team, user=viewer, role=TeamMembership.Role.VIEWER)
    return team


@pytest.fixture
def ticket(team):
    customer = Customer.objects.create(team=team, name="Amina Khan", email="amina@example.com")
    ticket = Ticket.objects.create(team=team, customer=customer, subject="Refund request")
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="I want a refund.",
    )
    return ticket


@pytest.fixture
def suggestion(ticket):
    return CopilotSuggestion.objects.create(
        ticket=ticket,
        suggestion_type=CopilotSuggestion.SuggestionType.REPLY_DRAFT,
        content="I can help review this refund request.",
        internal_notes="Refund approval is required.",
        needs_approval=True,
        proposed_sensitive_action="refund",
        model_name="local-heuristic",
        prompt_version="reply-draft-v1",
    )


def test_accept_sensitive_draft_creates_approval_request(client, agent, ticket, suggestion):
    client.force_login(agent)

    response = client.post(
        reverse("tickets:accept_suggestion", args=[ticket.id, suggestion.id]),
        {"content": "Please wait while we review this refund request."},
    )
    ticket.refresh_from_db()

    assert response.status_code == 302
    assert ticket.status == Ticket.Status.PENDING_INTERNAL
    assert ApprovalRequest.objects.filter(ticket=ticket, action_type="refund").exists()
    assert not ticket.messages.filter(sender_type=TicketMessage.SenderType.AGENT).exists()


def test_support_lead_can_view_and_approve_request(client, agent, lead, ticket, suggestion):
    client.force_login(agent)
    client.post(
        reverse("tickets:accept_suggestion", args=[ticket.id, suggestion.id]),
        {"content": "Please wait while we review this refund request."},
    )
    approval = ApprovalRequest.objects.get(ticket=ticket)

    client.force_login(lead)
    queue_response = client.get(reverse("approvals:queue"))
    approve_response = client.post(
        reverse("approvals:approve", args=[approval.id]),
        {"decision_note": "Approved by lead."},
    )
    approval.refresh_from_db()
    ticket.refresh_from_db()

    assert queue_response.status_code == 200
    assert b"Refund request" in queue_response.content
    assert approve_response.status_code == 302
    assert approval.status == ApprovalRequest.Status.APPROVED
    assert ticket.status == Ticket.Status.OPEN


def test_viewer_cannot_approve_request(client, agent, viewer, ticket, suggestion):
    client.force_login(agent)
    client.post(
        reverse("tickets:accept_suggestion", args=[ticket.id, suggestion.id]),
        {"content": "Please wait while we review this refund request."},
    )
    approval = ApprovalRequest.objects.get(ticket=ticket)

    client.force_login(viewer)
    response = client.post(
        reverse("approvals:reject", args=[approval.id]),
        {"decision_note": "No"},
    )
    approval.refresh_from_db()

    assert response.status_code == 403
    assert approval.status == ApprovalRequest.Status.PENDING

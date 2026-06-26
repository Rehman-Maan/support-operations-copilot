import pytest
from django.contrib.auth import get_user_model

from apps.approvals.models import ApprovalRequest
from apps.audit.models import AuditEvent
from apps.copilot.models import CopilotSuggestion
from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket
from services.approval_rules.approvals import create_approval_request, decide_approval
from services.approval_rules.detection import detect_sensitive_action


@pytest.fixture
def agent(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def lead(db):
    return get_user_model().objects.create_user(username="lead", password="test-pass")


@pytest.fixture
def team(agent, lead):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=agent)
    TeamMembership.objects.create(team=team, user=agent, role=TeamMembership.Role.SUPPORT_AGENT)
    TeamMembership.objects.create(team=team, user=lead, role=TeamMembership.Role.SUPPORT_LEAD)
    return team


@pytest.fixture
def ticket(team):
    customer = Customer.objects.create(team=team, name="Amina Khan", email="amina@example.com")
    return Ticket.objects.create(team=team, customer=customer, subject="Refund request")


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


def test_detect_sensitive_action_maps_suggestion_to_action_type(suggestion):
    assert detect_sensitive_action(suggestion) == ApprovalRequest.ActionType.REFUND


def test_create_approval_request_sets_ticket_pending_internal(agent, ticket, suggestion):
    approval = create_approval_request(
        suggestion=suggestion,
        requested_by=agent,
        edited_content="Please wait while we review this refund request.",
    )
    ticket.refresh_from_db()
    suggestion.refresh_from_db()

    assert approval is not None
    assert approval.action_type == ApprovalRequest.ActionType.REFUND
    assert approval.status == ApprovalRequest.Status.PENDING
    assert ticket.status == Ticket.Status.PENDING_INTERNAL
    assert suggestion.status == CopilotSuggestion.Status.ACCEPTED
    assert AuditEvent.objects.filter(ticket=ticket, event_type="approval_requested").exists()


def test_decide_approval_records_decision_and_reopens_ticket(agent, lead, ticket, suggestion):
    approval = create_approval_request(
        suggestion=suggestion,
        requested_by=agent,
        edited_content="Please wait while we review this refund request.",
    )

    decide_approval(
        approval=approval,
        reviewer=lead,
        status=ApprovalRequest.Status.APPROVED,
        decision_note="Approved after checking the policy.",
    )
    approval.refresh_from_db()
    ticket.refresh_from_db()

    assert approval.status == ApprovalRequest.Status.APPROVED
    assert approval.decided_by == lead
    assert ticket.status == Ticket.Status.OPEN
    assert AuditEvent.objects.filter(ticket=ticket, event_type="approval_approved").exists()

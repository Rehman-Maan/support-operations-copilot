from django.utils import timezone

from apps.approvals.models import ApprovalRequest
from apps.audit.models import AuditEvent
from apps.copilot.models import CopilotSuggestion
from apps.tickets.models import Ticket
from services.approval_rules.detection import detect_sensitive_action


def create_approval_request(
    *,
    suggestion: CopilotSuggestion,
    requested_by,
    edited_content: str,
) -> ApprovalRequest | None:
    action_type = detect_sensitive_action(suggestion)
    if not action_type:
        return None

    approval = ApprovalRequest.objects.create(
        ticket=suggestion.ticket,
        suggestion=suggestion,
        requested_by=requested_by,
        action_type=action_type,
        reason=suggestion.internal_notes or "Copilot draft marked this action for approval.",
        proposed_payload={
            "suggestion_id": suggestion.id,
            "reply_draft": edited_content,
            "model_name": suggestion.model_name,
            "prompt_version": suggestion.prompt_version,
            "proposed_sensitive_action": suggestion.proposed_sensitive_action,
        },
    )
    suggestion.status = CopilotSuggestion.Status.ACCEPTED
    suggestion.content = edited_content
    suggestion.accepted_by = requested_by
    suggestion.accepted_at = timezone.now()
    suggestion.save(update_fields=["status", "content", "accepted_by", "accepted_at"])

    ticket = suggestion.ticket
    ticket.transition_to(Ticket.Status.PENDING_INTERNAL)
    ticket.save(update_fields=["status", "closed_at", "updated_at"])
    AuditEvent.objects.create(
        team=ticket.team,
        ticket=ticket,
        actor_user=requested_by,
        actor_type=AuditEvent.ActorType.USER,
        event_type="approval_requested",
        payload={
            "approval_id": approval.id,
            "suggestion_id": suggestion.id,
            "action_type": action_type,
        },
    )
    return approval


def decide_approval(
    *,
    approval: ApprovalRequest,
    reviewer,
    status: str,
    decision_note: str = "",
) -> ApprovalRequest:
    if approval.status != ApprovalRequest.Status.PENDING:
        return approval

    approval.status = status
    approval.decided_by = reviewer
    approval.decision_note = decision_note
    approval.decided_at = timezone.now()
    approval.save(update_fields=["status", "decided_by", "decision_note", "decided_at"])

    event_type = (
        "approval_approved"
        if status == ApprovalRequest.Status.APPROVED
        else "approval_rejected"
    )
    AuditEvent.objects.create(
        team=approval.ticket.team,
        ticket=approval.ticket,
        actor_user=reviewer,
        actor_type=AuditEvent.ActorType.USER,
        event_type=event_type,
        payload={
            "approval_id": approval.id,
            "action_type": approval.action_type,
            "decision_note": decision_note,
        },
    )
    if approval.ticket.status == Ticket.Status.PENDING_INTERNAL:
        approval.ticket.transition_to(Ticket.Status.OPEN)
        approval.ticket.save(update_fields=["status", "closed_at", "updated_at"])
    return approval

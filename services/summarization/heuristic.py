from apps.approvals.models import ApprovalRequest
from apps.tickets.models import Ticket, TicketMessage


def summarize_with_heuristics(ticket: Ticket) -> dict:
    latest_customer_message = (
        ticket.messages.filter(sender_type=TicketMessage.SenderType.CUSTOMER)
        .order_by("-created_at")
        .first()
    )
    problem = latest_customer_message.body if latest_customer_message else ticket.subject
    pending_approval = ticket.approval_requests.filter(
        status=ApprovalRequest.Status.PENDING,
    ).first()

    summary = (
        f"Customer issue: {ticket.subject}. Latest customer detail: {problem} "
        f"Current status is {ticket.get_status_display()} with "
        f"{ticket.get_priority_display()} priority."
    )
    if ticket.intent:
        summary += f" Classified intent is {ticket.get_intent_display()}."
    if pending_approval:
        summary += f" Pending approval exists for {pending_approval.get_action_type_display()}."

    return {
        "summary": summary,
        "recommended_next_step": recommend_next_step(ticket),
        "unresolved_questions": unresolved_questions(ticket),
    }


def recommend_next_step(ticket: Ticket) -> str:
    pending_approval = ticket.approval_requests.filter(
        status=ApprovalRequest.Status.PENDING,
    ).first()
    if pending_approval:
        return f"Wait for support lead decision on {pending_approval.get_action_type_display()}."
    if ticket.needs_escalation:
        return "Escalate to a support lead before promising a sensitive outcome."
    if ticket.intent == Ticket.Intent.SHIPPING_DELAY:
        return "Check carrier tracking, confirm address, and send a delivery-status update."
    if ticket.intent == Ticket.Intent.ACCOUNT_ACCESS:
        return "Verify the account email and guide the customer through password recovery."
    if ticket.intent == Ticket.Intent.BILLING_ISSUE:
        return "Verify the payment record and prepare a credit-adjustment approval if needed."
    if ticket.status == Ticket.Status.PENDING_CUSTOMER:
        return "Wait for the customer response before taking the next action."
    return "Draft a policy-grounded reply and keep the ticket moving."


def unresolved_questions(ticket: Ticket) -> str:
    if ticket.intent == Ticket.Intent.REFUND_REQUEST:
        return "Order verification and refund approval decision are still needed."
    if ticket.intent == Ticket.Intent.SHIPPING_DELAY:
        return "Carrier status and current delivery estimate may still be missing."
    if ticket.intent == Ticket.Intent.COMPLAINT:
        return "Photos, product condition, and replacement eligibility may still be missing."
    if ticket.intent == Ticket.Intent.BILLING_ISSUE:
        return "Payment processor record and duplicate-charge confirmation may still be missing."
    return ""

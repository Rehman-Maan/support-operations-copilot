from apps.tickets.models import Ticket


def draft_with_heuristics(ticket: Ticket, context_blocks: list[str]) -> dict:
    latest_message = ticket.latest_message()
    customer_name = ticket.customer.name.split()[0] if ticket.customer.name else "there"
    context_available = bool(context_blocks)

    needs_approval = ticket.needs_escalation or ticket.intent in {
        Ticket.Intent.REFUND_REQUEST,
        Ticket.Intent.CANCELLATION,
        Ticket.Intent.BILLING_ISSUE,
    }
    action = _sensitive_action_for_ticket(ticket) if needs_approval else ""

    reply_parts = [
        f"Hi {customer_name},",
        "",
        "Thanks for reaching out. I understand the issue and I am sorry for the trouble.",
    ]
    if latest_message:
        reply_parts.append("I have reviewed the details you shared with our support team.")
    if context_available:
        reply_parts.append("Based on our support policy, we can review the next best step.")
    else:
        reply_parts.append(
            "I need to verify the relevant policy details before giving you a final answer."
        )
    if needs_approval:
        reply_parts.append(
            "This may require an internal approval before we can confirm the outcome."
        )
    reply_parts.extend(
        [
            "",
            "I will make sure this is checked carefully and will follow up with the next step.",
            "",
            "Best,",
            "Support Team",
        ]
    )

    notes = "Drafted locally from ticket metadata and retrieved policy context."
    if not context_available:
        notes += " No knowledge context was retrieved."

    return {
        "customer_reply": "\n".join(reply_parts),
        "internal_notes": notes,
        "needs_approval": needs_approval,
        "proposed_sensitive_action": action,
    }


def _sensitive_action_for_ticket(ticket: Ticket) -> str:
    if ticket.intent == Ticket.Intent.REFUND_REQUEST:
        return "refund"
    if ticket.intent == Ticket.Intent.CANCELLATION:
        return "cancellation"
    if ticket.intent == Ticket.Intent.BILLING_ISSUE:
        return "credit_adjustment"
    return "support_lead_review"

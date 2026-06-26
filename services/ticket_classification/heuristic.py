from apps.tickets.models import Ticket


def classify_with_heuristics(ticket_text: str) -> dict:
    text = ticket_text.lower()

    intent = Ticket.Intent.OTHER
    if any(word in text for word in ["refund", "money back", "return"]):
        intent = Ticket.Intent.REFUND_REQUEST
    elif any(word in text for word in ["shipping", "delivery", "tracking", "arrived", "package"]):
        intent = Ticket.Intent.SHIPPING_DELAY
    elif any(word in text for word in ["login", "password", "locked", "account access"]):
        intent = Ticket.Intent.ACCOUNT_ACCESS
    elif any(word in text for word in ["billing", "charged", "invoice", "payment"]):
        intent = Ticket.Intent.BILLING_ISSUE
    elif any(word in text for word in ["cancel", "cancellation"]):
        intent = Ticket.Intent.CANCELLATION
    elif any(word in text for word in ["bug", "error", "broken", "crash"]):
        intent = Ticket.Intent.BUG_REPORT
    elif any(word in text for word in ["complaint", "angry", "unacceptable"]):
        intent = Ticket.Intent.COMPLAINT

    urgent_terms = ["urgent", "immediately", "asap", "legal", "chargeback"]
    priority = Ticket.Priority.NORMAL
    if intent in _high_priority_intents():
        priority = Ticket.Priority.HIGH
    if any(term in text for term in urgent_terms):
        priority = Ticket.Priority.URGENT
    elif any(term in text for term in ["thanks", "question", "how do i"]):
        priority = Ticket.Priority.LOW

    sla_risk_level = Ticket.SlaRiskLevel.LOW
    if priority == Ticket.Priority.HIGH:
        sla_risk_level = Ticket.SlaRiskLevel.MEDIUM
    if priority == Ticket.Priority.URGENT:
        sla_risk_level = Ticket.SlaRiskLevel.HIGH
    elif priority == Ticket.Priority.LOW:
        sla_risk_level = Ticket.SlaRiskLevel.NONE

    sentiment = "neutral"
    if any(word in text for word in ["angry", "upset", "unacceptable"]):
        sentiment = "frustrated"
    needs_escalation = intent in _escalation_intents() or priority == Ticket.Priority.URGENT

    return {
        "intent": intent,
        "priority": priority,
        "sla_risk_level": sla_risk_level,
        "sentiment": sentiment,
        "needs_escalation": needs_escalation,
        "reason": "Classified locally from ticket keywords.",
    }


def _high_priority_intents() -> set[str]:
    return {
        Ticket.Intent.REFUND_REQUEST,
        Ticket.Intent.BILLING_ISSUE,
        Ticket.Intent.COMPLAINT,
    }


def _escalation_intents() -> set[str]:
    return {
        Ticket.Intent.REFUND_REQUEST,
        Ticket.Intent.CANCELLATION,
        Ticket.Intent.COMPLAINT,
    }

from apps.tickets.models import Ticket
from config.celery import app
from services.ticket_classification.classifier import classify_ticket as classify_ticket_service


@app.task
def classify_ticket(ticket_id: int) -> dict:
    ticket = Ticket.objects.select_related("team").get(id=ticket_id)
    result = classify_ticket_service(ticket)
    return {
        "ticket_id": ticket_id,
        "status": "classified",
        "intent": result.intent,
        "priority": result.priority,
        "sla_risk_level": result.sla_risk_level,
        "needs_escalation": result.needs_escalation,
    }

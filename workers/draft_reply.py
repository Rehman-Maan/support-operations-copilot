from apps.copilot.models import CopilotSuggestion
from apps.tickets.models import Ticket
from config.celery import app
from services.reply_drafting.drafter import draft_reply as draft_reply_service


@app.task
def draft_reply(ticket_id: int) -> dict:
    ticket = Ticket.objects.select_related("team", "customer").get(id=ticket_id)
    suggestion = draft_reply_service(ticket)
    return {
        "ticket_id": ticket_id,
        "suggestion_id": suggestion.id,
        "status": CopilotSuggestion.Status.PROPOSED,
        "needs_approval": suggestion.needs_approval,
    }

from apps.copilot.models import CopilotSuggestion
from apps.tickets.models import Ticket
from config.celery import app
from services.summarization.summarizer import summarize_ticket


@app.task
def summarize_thread(ticket_id: int) -> dict:
    ticket = Ticket.objects.select_related("team", "customer").get(id=ticket_id)
    suggestions = summarize_ticket(ticket)
    summary = suggestions["summary"]
    next_action = suggestions["next_action"]
    macro = suggestions["macro"]
    return {
        "ticket_id": ticket_id,
        "status": CopilotSuggestion.Status.PROPOSED,
        "summary_id": summary.id if summary else None,
        "next_action_id": next_action.id if next_action else None,
        "macro_suggestion_id": macro.id if macro else None,
    }

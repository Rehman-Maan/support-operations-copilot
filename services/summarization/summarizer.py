import json

from django.conf import settings

from apps.audit.models import AuditEvent
from apps.copilot.models import CopilotSuggestion
from apps.knowledge_base.models import Macro
from apps.tickets.models import Ticket
from services.pii_redaction.redactor import redact_text
from services.summarization.heuristic import summarize_with_heuristics
from services.summarization.parser import parse_summary
from services.summarization.prompts import SUMMARY_PROMPT
from services.summarization.schema import SUMMARY_SCHEMA


def summarize_ticket(ticket: Ticket) -> dict[str, CopilotSuggestion | None]:
    redacted_conversation, redaction_counts = build_redacted_conversation(ticket)
    result = _summarize_with_model_or_fallback(ticket, redacted_conversation)

    summary = _create_suggestion(
        ticket=ticket,
        suggestion_type=CopilotSuggestion.SuggestionType.SUMMARY,
        content=result.summary,
        internal_notes=result.unresolved_questions,
        model_name=result.model_name,
    )
    next_action = _create_suggestion(
        ticket=ticket,
        suggestion_type=CopilotSuggestion.SuggestionType.NEXT_ACTION,
        content=result.recommended_next_step,
        internal_notes="Recommended next step generated from the ticket conversation.",
        model_name=result.model_name,
    )
    macro_suggestion = recommend_macro(ticket)

    AuditEvent.objects.create(
        team=ticket.team,
        ticket=ticket,
        actor_type=AuditEvent.ActorType.AI,
        event_type="ticket_summarized",
        payload={
            "summary_id": summary.id,
            "next_action_id": next_action.id,
            "macro_suggestion_id": macro_suggestion.id if macro_suggestion else None,
            "model_name": result.model_name,
            "prompt_version": settings.TICKET_SUMMARY_PROMPT_VERSION,
            "redaction_counts": redaction_counts,
        },
    )
    return {
        "summary": summary,
        "next_action": next_action,
        "macro": macro_suggestion,
    }


def build_redacted_conversation(ticket: Ticket) -> tuple[str, dict[str, int]]:
    lines = [
        f"Subject: {ticket.subject}",
        f"Status: {ticket.status}",
        f"Priority: {ticket.priority}",
        f"Intent: {ticket.intent or 'unknown'}",
    ]
    counts: dict[str, int] = {}
    for message in ticket.messages.select_related("customer", "sender_user"):
        redacted = redact_text(message.body)
        lines.append(f"{message.sender_type}: {redacted.text}")
        if message.redacted_body != redacted.text:
            message.redacted_body = redacted.text
            message.save(update_fields=["redacted_body"])
        for label, count in redacted.counts.items():
            counts[label] = counts.get(label, 0) + count
    return "\n".join(lines), counts


def recommend_macro(ticket: Ticket) -> CopilotSuggestion | None:
    macro = (
        Macro.objects.filter(team=ticket.team, active=True, intent=ticket.intent)
        .order_by("name")
        .first()
    )
    if not macro:
        macro = Macro.objects.filter(team=ticket.team, active=True).order_by("name").first()
    if not macro:
        return None

    return _create_suggestion(
        ticket=ticket,
        suggestion_type=CopilotSuggestion.SuggestionType.MACRO,
        content=macro.body,
        internal_notes=f"Recommended macro: {macro.name}",
        model_name="local-macro-match",
    )


def _summarize_with_model_or_fallback(ticket: Ticket, redacted_conversation: str):
    if not settings.OPENAI_API_KEY:
        return parse_summary(summarize_with_heuristics(ticket), model_name="local-heuristic")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.responses.create(
            model=settings.OPENAI_SUMMARY_MODEL,
            input=SUMMARY_PROMPT.format(conversation=redacted_conversation),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ticket_summary",
                    "schema": SUMMARY_SCHEMA,
                    "strict": True,
                }
            },
        )
        return parse_summary(json.loads(response.output_text), settings.OPENAI_SUMMARY_MODEL)
    except Exception as exc:
        raw = summarize_with_heuristics(ticket)
        raw["unresolved_questions"] = (
            f"{raw['unresolved_questions']} OpenAI summary failed with "
            f"{type(exc).__name__}; used local fallback."
        ).strip()
        return parse_summary(raw, model_name="local-heuristic")


def _create_suggestion(
    *,
    ticket: Ticket,
    suggestion_type: str,
    content: str,
    internal_notes: str,
    model_name: str,
) -> CopilotSuggestion:
    return CopilotSuggestion.objects.create(
        ticket=ticket,
        suggestion_type=suggestion_type,
        content=content,
        internal_notes=internal_notes,
        model_name=model_name,
        prompt_version=settings.TICKET_SUMMARY_PROMPT_VERSION,
    )

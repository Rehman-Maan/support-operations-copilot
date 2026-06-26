import json

from django.conf import settings

from apps.audit.models import AuditEvent
from apps.copilot.models import CopilotSuggestion, RetrievedContext
from apps.tickets.models import Ticket
from services.pii_redaction.redactor import redact_text
from services.reply_drafting.heuristic import draft_with_heuristics
from services.reply_drafting.parser import parse_reply_draft
from services.reply_drafting.prompts import REPLY_DRAFT_PROMPT
from services.reply_drafting.schema import REPLY_DRAFT_SCHEMA
from services.retrieval.search import search_knowledge


def draft_reply(ticket: Ticket) -> CopilotSuggestion:
    redacted_ticket, redaction_counts = build_redacted_ticket_text(ticket)
    retrieved_chunks = list(search_knowledge(ticket.team, build_retrieval_query(ticket), limit=8))
    context_blocks = [
        _format_context_block(chunk, index)
        for index, chunk in enumerate(retrieved_chunks, 1)
    ]
    model_result = _draft_with_model_or_fallback(ticket, redacted_ticket, context_blocks)

    suggestion = CopilotSuggestion.objects.create(
        ticket=ticket,
        suggestion_type=CopilotSuggestion.SuggestionType.REPLY_DRAFT,
        content=model_result.customer_reply,
        internal_notes=model_result.internal_notes,
        needs_approval=model_result.needs_approval,
        proposed_sensitive_action=model_result.proposed_sensitive_action,
        model_name=model_result.model_name,
        prompt_version=settings.REPLY_DRAFT_PROMPT_VERSION,
    )
    for chunk in retrieved_chunks:
        RetrievedContext.objects.create(
            suggestion=suggestion,
            knowledge_chunk=chunk,
            relevance_score=float(getattr(chunk, "distance", 0.0) or 0.0),
            content_snapshot=chunk.content,
            source_title=chunk.document.title,
        )

    AuditEvent.objects.create(
        team=ticket.team,
        ticket=ticket,
        actor_type=AuditEvent.ActorType.AI,
        event_type="reply_draft_created",
        payload={
            "suggestion_id": suggestion.id,
            "model_name": model_result.model_name,
            "prompt_version": settings.REPLY_DRAFT_PROMPT_VERSION,
            "retrieved_chunk_ids": [chunk.id for chunk in retrieved_chunks],
            "redaction_counts": redaction_counts,
            "needs_approval": model_result.needs_approval,
            "proposed_sensitive_action": model_result.proposed_sensitive_action,
        },
    )
    return suggestion


def build_redacted_ticket_text(ticket: Ticket) -> tuple[str, dict[str, int]]:
    lines = [
        f"Subject: {ticket.subject}",
        f"Intent: {ticket.intent or 'unknown'}",
        f"Priority: {ticket.priority}",
        f"SLA risk: {ticket.sla_risk_level}",
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


def build_retrieval_query(ticket: Ticket) -> str:
    latest_message = ticket.latest_message()
    latest_body = latest_message.body if latest_message else ""
    return " ".join(
        part
        for part in [
            ticket.subject,
            ticket.intent,
            ticket.priority,
            latest_body,
        ]
        if part
    )


def _draft_with_model_or_fallback(
    ticket: Ticket,
    redacted_ticket: str,
    context_blocks: list[str],
):
    if not settings.OPENAI_API_KEY:
        raw = draft_with_heuristics(ticket, context_blocks)
        return parse_reply_draft(raw, model_name="local-heuristic")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.responses.create(
            model=settings.OPENAI_REPLY_MODEL,
            input=REPLY_DRAFT_PROMPT.format(
                ticket=redacted_ticket,
                context="\n\n".join(context_blocks) or "No relevant policy context was found.",
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "reply_draft",
                    "schema": REPLY_DRAFT_SCHEMA,
                    "strict": True,
                }
            },
        )
        return parse_reply_draft(json.loads(response.output_text), settings.OPENAI_REPLY_MODEL)
    except Exception as exc:
        raw = draft_with_heuristics(ticket, context_blocks)
        raw["internal_notes"] = (
            f"{raw['internal_notes']} OpenAI draft failed with {type(exc).__name__}; "
            "used local fallback."
        )
        return parse_reply_draft(raw, model_name="local-heuristic")


def _format_context_block(chunk, index: int) -> str:
    title = chunk.document.title
    section = f" - {chunk.section_title}" if chunk.section_title else ""
    return f"[Source {index}: {title}{section}]\n{chunk.content}"

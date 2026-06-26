import json

from django.conf import settings
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.tickets.models import Ticket
from services.pii_redaction.redactor import redact_text

from .heuristic import classify_with_heuristics
from .parser import ClassificationResult, parse_classification
from .prompts import CLASSIFICATION_PROMPT
from .schema import CLASSIFICATION_SCHEMA


def classify_ticket(ticket: Ticket) -> ClassificationResult:
    redacted_text, redaction_counts = build_redacted_ticket_text(ticket)
    raw_result = _classify_with_model_or_fallback(redacted_text)
    result = parse_classification(raw_result["payload"], model_name=raw_result["model_name"])

    ticket.intent = result.intent
    ticket.priority = result.priority
    ticket.sla_risk_level = result.sla_risk_level
    ticket.sentiment = result.sentiment
    ticket.needs_escalation = result.needs_escalation
    ticket.classification_reason = result.reason
    ticket.classified_at = timezone.now()
    ticket.save(
        update_fields=[
            "intent",
            "priority",
            "sla_risk_level",
            "sentiment",
            "needs_escalation",
            "classification_reason",
            "classified_at",
            "updated_at",
        ]
    )

    AuditEvent.objects.create(
        team=ticket.team,
        ticket=ticket,
        actor_type=AuditEvent.ActorType.AI,
        event_type="ticket_classified",
        payload={
            "model_name": result.model_name,
            "prompt_version": settings.TICKET_CLASSIFICATION_PROMPT_VERSION,
            "classification": {
                "intent": result.intent,
                "priority": result.priority,
                "sla_risk_level": result.sla_risk_level,
                "sentiment": result.sentiment,
                "needs_escalation": result.needs_escalation,
                "reason": result.reason,
            },
            "redaction_counts": redaction_counts,
        },
    )
    return result


def build_redacted_ticket_text(ticket: Ticket) -> tuple[str, dict[str, int]]:
    parts = [f"Subject: {ticket.subject}"]
    total_counts: dict[str, int] = {}

    for message in ticket.messages.order_by("created_at"):
        result = redact_text(message.body)
        if message.redacted_body != result.text:
            message.redacted_body = result.text
            message.save(update_fields=["redacted_body"])
        for label, count in result.counts.items():
            total_counts[label] = total_counts.get(label, 0) + count
        parts.append(f"{message.get_sender_type_display()}: {result.text}")

    return "\n".join(parts), total_counts


def _classify_with_model_or_fallback(redacted_text: str) -> dict:
    if not settings.OPENAI_API_KEY:
        return {
            "model_name": "local-heuristic",
            "payload": classify_with_heuristics(redacted_text),
        }

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.responses.create(
            model=settings.OPENAI_CLASSIFICATION_MODEL,
            input=CLASSIFICATION_PROMPT.format(ticket_text=redacted_text),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ticket_classification",
                    "schema": CLASSIFICATION_SCHEMA,
                    "strict": True,
                }
            },
        )
        return {
            "model_name": settings.OPENAI_CLASSIFICATION_MODEL,
            "payload": response.output_text,
        }
    except Exception as exc:
        fallback = classify_with_heuristics(redacted_text)
        fallback["reason"] = f"{fallback['reason']} OpenAI fallback reason: {type(exc).__name__}."
        return {
            "model_name": f"{settings.OPENAI_CLASSIFICATION_MODEL}+local-fallback",
            "payload": json.dumps(fallback),
        }

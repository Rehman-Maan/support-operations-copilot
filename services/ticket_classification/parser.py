import json
from dataclasses import dataclass

from apps.tickets.models import Ticket


@dataclass(frozen=True)
class ClassificationResult:
    intent: str
    priority: str
    sla_risk_level: str
    sentiment: str
    needs_escalation: bool
    reason: str
    model_name: str


def parse_classification(raw: str | dict, model_name: str) -> ClassificationResult:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(payload, dict):
        raise ValueError("Classification output must be a JSON object.")

    intent = _allowed(payload.get("intent"), Ticket.Intent.values, Ticket.Intent.OTHER)
    priority = _allowed(payload.get("priority"), Ticket.Priority.values, Ticket.Priority.NORMAL)
    sla_risk = _allowed(
        payload.get("sla_risk_level"),
        Ticket.SlaRiskLevel.values,
        Ticket.SlaRiskLevel.NONE,
    )

    return ClassificationResult(
        intent=intent,
        priority=priority,
        sla_risk_level=sla_risk,
        sentiment=str(payload.get("sentiment") or "neutral")[:64],
        needs_escalation=bool(payload.get("needs_escalation", False)),
        reason=str(payload.get("reason") or "").strip(),
        model_name=model_name,
    )


def _allowed(value, allowed_values, default: str) -> str:
    return value if value in allowed_values else default

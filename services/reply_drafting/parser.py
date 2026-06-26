from dataclasses import dataclass


@dataclass(frozen=True)
class ReplyDraftResult:
    customer_reply: str
    internal_notes: str
    needs_approval: bool
    proposed_sensitive_action: str
    model_name: str


def parse_reply_draft(raw: dict, model_name: str) -> ReplyDraftResult:
    return ReplyDraftResult(
        customer_reply=str(raw.get("customer_reply", "")).strip(),
        internal_notes=str(raw.get("internal_notes", "")).strip(),
        needs_approval=bool(raw.get("needs_approval", False)),
        proposed_sensitive_action=str(raw.get("proposed_sensitive_action", "")).strip(),
        model_name=model_name,
    )

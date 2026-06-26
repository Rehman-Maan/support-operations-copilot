from apps.approvals.models import ApprovalRequest
from apps.copilot.models import CopilotSuggestion

SENSITIVE_ACTION_ALIASES = {
    "refund": ApprovalRequest.ActionType.REFUND,
    "refunds": ApprovalRequest.ActionType.REFUND,
    "cancellation": ApprovalRequest.ActionType.CANCELLATION,
    "cancel": ApprovalRequest.ActionType.CANCELLATION,
    "account_closure": ApprovalRequest.ActionType.ACCOUNT_CLOSURE,
    "close_account": ApprovalRequest.ActionType.ACCOUNT_CLOSURE,
    "credit": ApprovalRequest.ActionType.CREDIT_ADJUSTMENT,
    "credit_adjustment": ApprovalRequest.ActionType.CREDIT_ADJUSTMENT,
    "data_export": ApprovalRequest.ActionType.DATA_EXPORT,
    "data_deletion": ApprovalRequest.ActionType.DATA_DELETION,
    "delete_data": ApprovalRequest.ActionType.DATA_DELETION,
    "support_lead_review": ApprovalRequest.ActionType.SUPPORT_LEAD_REVIEW,
}


def detect_sensitive_action(suggestion: CopilotSuggestion) -> str:
    if not suggestion.needs_approval:
        return ""
    action = suggestion.proposed_sensitive_action.strip().lower().replace(" ", "_")
    return SENSITIVE_ACTION_ALIASES.get(action, ApprovalRequest.ActionType.SUPPORT_LEAD_REVIEW)

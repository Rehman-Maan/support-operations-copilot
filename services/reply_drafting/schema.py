REPLY_DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "customer_reply": {
            "type": "string",
            "description": "A customer-facing draft that the agent can edit before sending.",
        },
        "internal_notes": {
            "type": "string",
            "description": "Private guidance for the agent. Do not include hidden policy IDs.",
        },
        "needs_approval": {
            "type": "boolean",
            "description": "Whether a human approval request may be needed before sending.",
        },
        "proposed_sensitive_action": {
            "type": "string",
            "description": "One short sensitive action label, or an empty string.",
        },
    },
    "required": [
        "customer_reply",
        "internal_notes",
        "needs_approval",
        "proposed_sensitive_action",
    ],
    "additionalProperties": False,
}

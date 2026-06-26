CLASSIFICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "refund_request",
                "shipping_delay",
                "product_question",
                "account_access",
                "billing_issue",
                "cancellation",
                "bug_report",
                "complaint",
                "other",
            ],
        },
        "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]},
        "sla_risk_level": {"type": "string", "enum": ["none", "low", "medium", "high"]},
        "sentiment": {"type": "string"},
        "needs_escalation": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": [
        "intent",
        "priority",
        "sla_risk_level",
        "sentiment",
        "needs_escalation",
        "reason",
    ],
}

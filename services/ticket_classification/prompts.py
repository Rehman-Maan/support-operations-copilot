CLASSIFICATION_PROMPT = """You are a support operations classifier.

Classify the ticket using only the provided ticket text.

Return valid JSON with:
- intent
- priority
- sla_risk_level
- sentiment
- needs_escalation
- reason

Allowed intents:
refund_request, shipping_delay, product_question, account_access,
billing_issue, cancellation, bug_report, complaint, other

Allowed priorities:
low, normal, high, urgent

Allowed SLA risk levels:
none, low, medium, high

Ticket:
{ticket_text}
"""

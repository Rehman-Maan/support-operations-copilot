SUMMARY_PROMPT = """You are summarizing a support ticket for a human support agent.

Create a concise internal summary.

Include:
- customer problem
- important facts
- actions already taken
- unresolved questions
- recommended next step

Do not add facts that are not present in the conversation.

Conversation:
{conversation}

Return:
- summary
- recommended_next_step
- unresolved_questions
"""

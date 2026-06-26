SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "Concise internal ticket summary for the support agent.",
        },
        "recommended_next_step": {
            "type": "string",
            "description": "One concrete next action for the agent.",
        },
        "unresolved_questions": {
            "type": "string",
            "description": "Open questions or missing facts, or an empty string.",
        },
    },
    "required": ["summary", "recommended_next_step", "unresolved_questions"],
    "additionalProperties": False,
}

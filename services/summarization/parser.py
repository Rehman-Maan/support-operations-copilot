from dataclasses import dataclass


@dataclass(frozen=True)
class SummaryResult:
    summary: str
    recommended_next_step: str
    unresolved_questions: str
    model_name: str


def parse_summary(raw: dict, model_name: str) -> SummaryResult:
    return SummaryResult(
        summary=str(raw.get("summary", "")).strip(),
        recommended_next_step=str(raw.get("recommended_next_step", "")).strip(),
        unresolved_questions=str(raw.get("unresolved_questions", "")).strip(),
        model_name=model_name,
    )

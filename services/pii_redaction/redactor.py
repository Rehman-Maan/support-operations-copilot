import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RedactionResult:
    text: str
    counts: dict[str, int] = field(default_factory=dict)


PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "card": re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)"),
    "phone": re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"),
    "api_key": re.compile(r"\b(?:sk|pk|rk|api)[-_][A-Za-z0-9_-]{16,}\b"),
    "order_id": re.compile(r"\b(?:order|ord|invoice|inv)[\s:#-]*[A-Z0-9-]{5,}\b", re.IGNORECASE),
}


def redact_text(text: str) -> RedactionResult:
    redacted = text
    counts: dict[str, int] = {}

    for label, pattern in PATTERNS.items():
        redacted, count = pattern.subn(f"[REDACTED_{label.upper()}]", redacted)
        if count:
            counts[label] = count

    return RedactionResult(text=redacted, counts=counts)

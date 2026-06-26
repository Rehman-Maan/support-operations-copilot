import json
import time
from pathlib import Path

from django.conf import settings

from apps.evaluations.models import EvaluationRun
from apps.teams.models import Team
from services.ticket_classification.heuristic import classify_with_heuristics


def run_support_case_evaluation(dataset_name: str, team: Team) -> EvaluationRun:
    started = time.perf_counter()
    cases = _load_dataset(dataset_name)
    failed_cases: list[dict] = []

    intent_correct = 0
    priority_correct = 0
    true_positive = 0
    false_positive = 0
    false_negative = 0
    grounded_scores: list[float] = []

    for case in cases:
        text = _case_text(case)
        predicted = classify_with_heuristics(text)

        if predicted["intent"] == case["expected_intent"]:
            intent_correct += 1
        else:
            failed_cases.append(
                {
                    "id": case["id"],
                    "reason": (
                        f"Intent expected {case['expected_intent']} but got "
                        f"{predicted['intent']}."
                    ),
                }
            )

        if predicted["priority"] == case["expected_priority"]:
            priority_correct += 1

        expected_escalation = bool(case["expected_needs_escalation"])
        predicted_escalation = bool(predicted["needs_escalation"])
        if predicted_escalation and expected_escalation:
            true_positive += 1
        elif predicted_escalation and not expected_escalation:
            false_positive += 1
        elif expected_escalation and not predicted_escalation:
            false_negative += 1

        grounded_scores.append(_score_groundedness(case, predicted))

    case_count = len(cases) or 1
    intent_accuracy = intent_correct / case_count
    priority_accuracy = priority_correct / case_count
    classifier_f1 = (intent_accuracy + priority_accuracy) / 2
    escalation_precision = _safe_divide(true_positive, true_positive + false_positive)
    escalation_recall = _safe_divide(true_positive, true_positive + false_negative)
    groundedness_score = sum(grounded_scores) / len(grounded_scores) if grounded_scores else 0.0
    average_latency_ms = ((time.perf_counter() - started) * 1000) / case_count

    return EvaluationRun.objects.create(
        team=team,
        name="Support case smoke evaluation",
        dataset_name=dataset_name,
        model_name="local-heuristic",
        classifier_f1=classifier_f1,
        escalation_precision=escalation_precision,
        escalation_recall=escalation_recall,
        groundedness_score=groundedness_score,
        average_latency_ms=average_latency_ms,
        case_count=len(cases),
        failed_cases=failed_cases,
    )


def _load_dataset(dataset_name: str) -> list[dict]:
    dataset_path = Path(settings.BASE_DIR) / "eval" / "datasets" / dataset_name
    with dataset_path.open(encoding="utf-8") as file:
        return json.load(file)


def _case_text(case: dict) -> str:
    messages = " ".join(message["text"] for message in case.get("messages", []))
    return f"{case['subject']} {messages}"


def _score_groundedness(case: dict, predicted: dict) -> float:
    score = 0.0
    if case.get("expected_sensitive_action") and predicted["needs_escalation"]:
        score += 0.5
    elif not case.get("expected_sensitive_action"):
        score += 0.5

    notes = " ".join(case.get("ideal_reply_notes", [])).lower()
    reason = str(predicted.get("reason", "")).lower()
    if any(token in f"{notes} {reason}" for token in ["approval", "tracking", "verify"]):
        score += 0.5
    return score


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator

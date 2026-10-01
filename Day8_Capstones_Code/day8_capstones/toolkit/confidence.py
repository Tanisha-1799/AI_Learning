"""
toolkit/confidence.py

Translates a raw retrieval relevance score into a High/Medium/Low/Refused
confidence level, and makes the refusal decision explicit and tunable.
Thresholds here are DEFAULTS — each capstone scenario should decide, and
justify, its own values.
"""

HIGH_THRESHOLD = 0.5
MEDIUM_THRESHOLD = 0.3


def confidence_level(best_score, high=HIGH_THRESHOLD, medium=MEDIUM_THRESHOLD) -> str:
    if best_score is None:
        return "Refused"
    if best_score >= high:
        return "High"
    if best_score >= medium:
        return "Medium"
    return "Low"


def should_refuse(best_score, medium=MEDIUM_THRESHOLD) -> bool:
    return best_score is None or best_score < medium


def best_score_from_results(results: list) -> float:
    scores = [score for _, score in results if score is not None]
    return max(scores) if scores else None

"""
toolkit/output_validation.py

Schema/content checks run on a generated answer before it's delivered.
"""
import re
from pii import contains_pii
from injection_defense import scan_for_injection

CITATION_PATTERN = re.compile(r"\(Source:\s*[^)]+\)", re.IGNORECASE)
REFUSAL_MARKERS = ["i don't know", "cannot", "not able to", "no relevant"]


def is_refusal(answer: str) -> bool:
    lower = answer.lower()
    return any(marker in lower for marker in REFUSAL_MARKERS)


def validate_answer(answer: str) -> dict:
    checks = {}
    checks["not_empty"] = bool(answer and answer.strip())
    refusal = is_refusal(answer)
    checks["has_citation_or_is_refusal"] = refusal or bool(CITATION_PATTERN.search(answer))
    checks["no_leaked_pii"] = not contains_pii(answer)
    injection_phrases = scan_for_injection(answer)
    checks["no_injection_phrasing"] = len(injection_phrases) == 0

    passed = all(checks.values())
    failed_checks = [name for name, ok in checks.items() if not ok]
    details = "All checks passed." if passed else f"Failed: {', '.join(failed_checks)}"
    return {"passed": passed, "checks": checks, "details": details}


FALLBACK_MESSAGE = (
    "I'm not able to deliver a response to this question right now — it "
    "did not pass an internal safety check. Please rephrase your question "
    "or contact support if this persists."
)

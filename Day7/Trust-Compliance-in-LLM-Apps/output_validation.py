"""
output_validation.py

Pramaan — Output Validation: Schema Checks & Content Filters Before Delivery
================================================================================
Everything so far has focused on controlling what goes INTO the LLM.
This module checks what comes OUT, before it's ever returned to a user —
the last line of defence, catching problems that slipped past every
earlier stage.

Four checks, all fast and deterministic (no extra LLM call needed):

  1. Not empty — an answer must actually contain something.
  2. Citation present — if the answer isn't a refusal, it must contain at
     least one (Source: ...) citation, per the system prompt's own rule.
  3. No leaked PII — re-run the SAME PII patterns from pii.py against the
     OUTPUT, not just the input. A model can occasionally echo something
     PII-shaped back from its context.
  4. No unresolved injection phrasing — if the answer itself contains a
     phrase from injection_defense.py's suspicious pattern list, that's a
     strong signal something upstream didn't hold.

If any check fails, app.py does NOT deliver the generated answer — it
substitutes a safe fallback message and logs the validation failure.
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
    """Runs all four checks and returns a report:
    {"passed": bool, "checks": {...}, "details": str}
    `passed` is True only if every applicable check passes."""
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
    if injection_phrases:
        details += f" (suspicious phrases in answer: {injection_phrases})"

    return {"passed": passed, "checks": checks, "details": details}


FALLBACK_MESSAGE = (
    "I'm not able to deliver a response to this question right now — it "
    "did not pass an internal safety check. Please rephrase your question "
    "or contact support if this persists."
)

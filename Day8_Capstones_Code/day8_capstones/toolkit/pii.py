"""
toolkit/pii.py

PII detection and redaction — usable at ingest, on incoming questions,
and on outgoing answers. Pattern-based (email, Indian phone numbers,
PAN-style IDs) — not a substitute for a real NER-based detector.
"""
import re

PATTERNS = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE_INDIA": re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}\b"),
    "PAN_LIKE_ID": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
}


def redact_pii(text: str) -> tuple[str, dict]:
    redaction_counts = {}
    redacted_text = text
    for label, pattern in PATTERNS.items():
        matches = pattern.findall(redacted_text)
        if matches:
            redaction_counts[label] = len(matches)
            redacted_text = pattern.sub(f"[REDACTED_{label}]", redacted_text)
    return redacted_text, redaction_counts


def contains_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern in PATTERNS.values())

"""
pii.py

Pramaan — PII Detection & Redaction (Ingest AND Serving Time)
==================================================================
Disha (Day 5) used this only during ingestion — scrubbing PII out of
documents before they were embedded. Pramaan calls the SAME function at
two more points, because PII can enter or leave the pipeline in more
than one place:

  1. INGEST TIME  (build_vectorstore.py) — redact PII in source documents
     before they're chunked and embedded, same as Disha.
  2. SERVING TIME, on the way IN (app.py) — a user might paste PII into
     their own question ("my number is 98765..., can you check my
     incident status?"). That should never reach the LLM or the audit
     log in raw form.
  3. SERVING TIME, on the way OUT (app.py, via output_validation.py) —
     even with clean inputs, a model can occasionally echo back something
     PII-shaped from its context. The output gets scanned too, as a last
     line of defence, not just the input.

This is intentionally still a simple, regex-based approach — not a
substitute for a real NER-based PII detector in production. See the
Disha lab's original caveat: this catches PII with a predictable SHAPE
(an email always has an @), not PII expressed as plain prose (a name).
"""
import re

PATTERNS = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE_INDIA": re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}\b"),
    "PAN_LIKE_ID": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
}


def redact_pii(text: str) -> tuple[str, dict]:
    """Replace any matched PII with a labelled placeholder.
    Returns the redacted text AND a count of what was redacted, so callers
    can report what happened without ever printing the actual PII."""
    redaction_counts = {}
    redacted_text = text
    for label, pattern in PATTERNS.items():
        matches = pattern.findall(redacted_text)
        if matches:
            redaction_counts[label] = len(matches)
            redacted_text = pattern.sub(f"[REDACTED_{label}]", redacted_text)
    return redacted_text, redaction_counts


def contains_pii(text: str) -> bool:
    """Quick boolean check, used where callers just need to know WHETHER
    to flag something, without needing the full redacted text back."""
    return any(pattern.search(text) for pattern in PATTERNS.values())

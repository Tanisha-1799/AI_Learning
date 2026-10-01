"""
agent.py

Nyaya - Ask the Pipeline (Step 3 of 3)
======================================
5 hardcoded questions, one per source document / format, so a single run
proves Nyaya is grounded across ALL FIVE formats (PDF, Word, HTML, CSV,
JSON) — not just whichever one happened to be easiest to parse.

IMPORTANT: app.py must already be running in a separate terminal
(uvicorn app:app --reload --port 8000) before you run this file.

Run:
    python agent.py
"""
import os
from urllib.parse import urlsplit, urlunsplit

import requests

BASE_URL = os.getenv("NYAYA_BASE_URL", "http://localhost:8000/ask")

# One question per document/format, in the same order as documents/.
QUESTIONS = [
    "What is the limitation of liability cap in our standard MSA?",                         # PDF (MSA)
    "What is the deadline for submitting the quarterly compliance report?",                  # Word (circular)
    "Who do I contact to request an urgent contract review?",                                # HTML (FAQ) — tests PII redaction
    "Which compliance audit findings are still open?",                                       # CSV (audit log)
    "Which regulatory filings are overdue or due within the next 30 days?",                 # JSON (filing tracker)
]

BONUS_QUESTION = "Which regulatory filings are overdue or due within the next 30 days?"


def ask_nyaya(question: str, pattern: str = "topk", k: int = 3) -> dict:
    response = requests.get(BASE_URL, params={"q": question, "pattern": pattern, "k": k}, timeout=60)
    response.raise_for_status()
    return response.json()


def check_backend_identity() -> None:
    """Warn if configured BASE_URL host/port is not serving Nyaya."""
    try:
        parsed = urlsplit(BASE_URL)
        root_url = urlunsplit((parsed.scheme, parsed.netloc, "/", "", ""))
        response = requests.get(root_url, timeout=10)
        response.raise_for_status()
        payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        message = str(payload.get("message", ""))
        if "Nyaya" not in message:
            print("WARNING: Configured backend does not look like Nyaya.")
            print(f"         Root message: {message or '(none)'}")
            print(f"         Root URL checked: {root_url}")
            print("         Start Nyaya app.py on this port, or update NYAYA_BASE_URL.")
    except Exception:
        # Normal error handling is already done in the main ask loop.
        pass


def main():
    print("=" * 60)
    print("Nyaya - NCS Telco+ Legal and Compliance Document Intelligence")
    print("=" * 60)
    print(f"Backend: {BASE_URL}")

    check_backend_identity()

    for i, question in enumerate(QUESTIONS, start=1):
        print(f"\nQ{i}: {question}")
        try:
            result = ask_nyaya(question)
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not reach Nyaya. Is app.py running in another "
                  "terminal? (uvicorn app:app --reload --port 8000)")
            return
        except requests.exceptions.HTTPError as exc:
            print(f"ERROR: Nyaya backend returned {exc.response.status_code}.")
            try:
                print(f"Detail: {exc.response.json()}")
            except Exception:
                print(f"Detail: {exc.response.text}")
            return

        if not result["retrieved_chunks"]:
            print("  (No chunks cleared the confidence threshold.)")
        for chunk in result["retrieved_chunks"]:
            score = chunk.get("relevance_score", chunk.get("score", "n/a"))
            metadata = chunk.get("metadata", {})
            source = chunk.get("source", "unknown")
            preview = chunk.get("text_preview", "")
            print(f"    - {source}  (score={score})  metadata={metadata}")
            print(f"      \"{preview}\"")

        print(f"\nA{i}: {result['answer']}")
        print(f"     (Sources: {', '.join(result['sources']) if result['sources'] else 'none'})")

    print("\n" + "=" * 60)
    print("BONUS - comparing retrieval patterns on ONE question")
    print("=" * 60)
    print(f"Question: {BONUS_QUESTION}\n")
    for pattern in ["topk", "threshold"]:
        print(f"--- Pattern: {pattern} ---")
        result = ask_nyaya(BONUS_QUESTION, pattern=pattern)
        print(f"Chunks retrieved: {len(result['retrieved_chunks'])}")
        for chunk in result["retrieved_chunks"]:
            score = chunk.get("relevance_score", chunk.get("score", "n/a"))
            print(f"    - {chunk.get('source', 'unknown')} (score={score})")
        print(f"Answer preview: {result['answer'][:150]}...\n")

    print("=" * 60)
    print("Done! Try editing QUESTIONS above, or the chunking strategy used")
    print("to build the store, to see how retrieval quality changes.")
    print("=" * 60)


if __name__ == "__main__":
    main()

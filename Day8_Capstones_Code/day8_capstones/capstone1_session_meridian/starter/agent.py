"""
starter/agent.py — Meridian Freight & Logistics

Run AFTER app.py is running (uvicorn app:app --reload --port 8000):
    python agent.py

These 5 questions are deliberately chosen to stress-test your Part 1
predictions — read what each one is really testing before you conclude
your implementation "works."
"""
import requests

BASE_URL = "http://localhost:8000/ask"

QUESTIONS = [
    # Tests: heading-aware chunking + version metadata + citation
    # requirement. The correct answer must come from the CURRENT
    # version (4.0) rule, not an older cached version.
    "Who approves a sick leave extension beyond 5 days, and what policy version is that rule from?",

    # Tests: hybrid retrieval. "MFL-BLR-03" and "Band B" are exact
    # strings — does your retrieval find the right CSV row reliably?
    "What is the pay band range for a Shift Supervisor (Band B) at the Bengaluru East Depot, location code MFL-BLR-03?",

    # Tests: PII redaction on the way IN — this question itself
    # contains a phone number.
    "My callback number is 9123456780 — who do I contact about a sick leave extension?",

    # Tests: JSON loading + a scenario requiring cross-referencing two
    # facts (tenure requirement AND deadline) from the same record.
    "What is the minimum tenure required to apply for the open Shift Supervisor position at Bengaluru East Depot, and what's the application deadline?",

    # Tests: the refusal guardrail — nothing in these 4 documents
    # covers this.
    "What is Meridian's policy on remote work for head-office staff?",
]


def ask(question: str, **params) -> dict:
    response = requests.get(BASE_URL, params={"q": question, **params}, timeout=60)
    response.raise_for_status()
    return response.json()


def main():
    print("=" * 60)
    print("Meridian Freight & Logistics HR Assistant — Test Run")
    print("=" * 60)

    for i, question in enumerate(QUESTIONS, start=1):
        print(f"\nQ{i}: {question}")
        try:
            result = ask(question)
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not reach the app. Is app.py running? "
                  "(uvicorn app:app --reload --port 8000)")
            return
        print(f"Confidence: {result.get('confidence')}")
        print(f"Answer: {result.get('answer')}")
        print(f"Sources: {result.get('sources')}")

    print("\n" + "=" * 60)
    print("Now go to Part 3 of the worksheet: did the results match")
    print("what you predicted in Part 1? Where were you surprised?")
    print("=" * 60)


if __name__ == "__main__":
    main()

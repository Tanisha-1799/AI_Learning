"""
agent.py

Pramaan — Ask the Trust-Wired Pipeline (Step 3 of 3)
=========================================================
5 hardcoded domain questions (same coverage as Disha), PLUS 3 dedicated
demo questions that specifically exercise the trust stack: PII redaction
on the way in, prompt-injection detection on real retrieved content, and
a refusal for an out-of-scope question.

IMPORTANT: app.py must already be running in a separate terminal
(uvicorn app:app --reload --port 8000) before you run this file.

Run:
    python agent.py
"""
import requests

BASE_URL = "http://localhost:8000/ask"

DOMAIN_QUESTIONS = [
    "What is the maximum indoor EIRP for Band 78 deployments?",
    "What service credit applies if uptime falls below the SLA guarantee?",
    "Which incidents in the log are still Open?",
    "Which vendor's equipment is NOT approved for indoor deployment, and why?",
    "What is the target resolution time for a P1 incident?",
]

# Deliberately includes a phone number, to demonstrate serving-time PII
# redaction on the QUESTION itself, before it's logged or sent anywhere.
PII_DEMO_QUESTION = (
    "My callback number is 9876543210 — who do I contact for a P1 "
    "escalation outside business hours?"
)

# This retrieves the security-awareness FAQ section that was deliberately
# written to contain injection-style phrasing — a real end-to-end test,
# not a synthetic one.
INJECTION_DEMO_QUESTION = "What should I do if I receive a suspicious support request?"

# No document covers this at all — should trigger the refusal guardrail.
OUT_OF_SCOPE_QUESTION = "What is our company's quarterly revenue for this year?"


def ask(question: str, **params) -> dict:
    response = requests.get(BASE_URL, params={"q": question, **params}, timeout=60)
    response.raise_for_status()
    return response.json()


def print_result(label: str, result: dict):
    print(f"\n{label}")
    print(f"Question (as logged) : {result['question']}")
    print(f"Confidence            : {result['confidence']}")
    print(f"Injection flagged     : {result['injection_flagged']}")
    if result.get("injection_details"):
        print(f"Injection details     : {result['injection_details']}")
    print(f"Output validation OK  : {result['output_validation_passed']}")
    print(f"Answer                : {result['answer']}")
    print(f"Sources               : {result['sources']}")
    print(f"Trace (per-stage sec) : {result['trace']}")


def main():
    print("=" * 64)
    print("Pramaan — NCS Telco+ Trust & Compliance RAG Pipeline")
    print("=" * 64)

    for i, question in enumerate(DOMAIN_QUESTIONS, start=1):
        try:
            result = ask(question)
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not reach Pramaan. Is app.py running in another "
                  "terminal? (uvicorn app:app --reload --port 8000)")
            return
        print_result(f"Q{i}: {question}", result)

    print("\n" + "=" * 64)
    print("TRUST-STACK DEMONSTRATIONS")
    print("=" * 64)

    result = ask(PII_DEMO_QUESTION)
    print_result("PII DEMO — a phone number in the question itself", result)
    print("Notice: the question ABOVE should show [REDACTED_PHONE_INDIA],")
    print("not the real number you sent — that's serving-time redaction.")

    result = ask(INJECTION_DEMO_QUESTION)
    print_result("INJECTION DEMO — retrieves a real FAQ section with injection-style text", result)
    print("Notice: injection_flagged should be True, with the exact phrases found —")
    print("and the answer should still just be a normal, safe FAQ answer.")

    result = ask(OUT_OF_SCOPE_QUESTION)
    print_result("REFUSAL DEMO — a question no document covers", result)
    print("Notice: confidence should be 'Refused', and no LLM call happened at all.")

    print("\n" + "=" * 64)
    print("Done! Run audit_query_tool.py next to see everything above")
    print("as real, queryable rows in the audit log.")
    print("=" * 64)


if __name__ == "__main__":
    main()

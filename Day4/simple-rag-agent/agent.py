"""
agent.py

Saathi — the NCS Telco+ HR Policy Assistant
============================================
Step 3 of 3: talk to Saathi.

This script plays the role of an employee asking Saathi 5 questions — one
drawn from each of the 5 HR policies — and prints Saathi's grounded answers
along with which policy document(s) each answer came from.

IMPORTANT: app.py must already be running in a separate terminal
(uvicorn app:app --reload --port 8000) before you run this file.

Run with:
    python agent.py
"""
import requests

BASE_URL = "http://localhost:8000/ask"

# One hardcoded question per policy, so a single run demonstrates that
# Saathi is grounded across the WHOLE knowledge base, not just one document.
QUESTIONS = [
    "How many casual leaves am I entitled to in a year?",                      # Leave Policy
    "Can I work from home permanently, or only a few days a week?",             # WFH/Hybrid Policy
    "Who do I contact if I want to raise a harassment complaint?",              # Code of Conduct
    "What is the maximum amount I can claim per day for client-site travel?",   # Travel & Reimbursement
    "How often is my performance reviewed, and who makes the final promotion decision?",  # Performance Review
    "Can I do work from home once a week?",
    "Will company reiumburse my taxi or flight fair when I travel to my hometown?",
    "If I am on notice period, can I take a leave?",
    "How my performance is evaluated?"
]


def ask_saathi(question: str) -> dict:
    response = requests.get(BASE_URL, params={"q": question}, timeout=60)
    response.raise_for_status()
    return response.json()


def main():
    print("=" * 60)
    print("Saathi — NCS Telco+ HR Policy Assistant")
    print("=" * 60)

    for i, question in enumerate(QUESTIONS, start=1):
        print(f"\nQ{i}: {question}")
        try:
            result = ask_saathi(question)
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not reach Saathi. Is app.py running in another "
                  "terminal? (uvicorn app:app --reload --port 8000)")
            return
        except requests.exceptions.HTTPError as exc:
            print(f"ERROR: Saathi backend returned {exc.response.status_code}.")
            try:
                print(f"Detail: {exc.response.json()}")
            except Exception:
                print(f"Detail: {exc.response.text}")
            return

        print("  Retrieved from the vector store (this is the metadata driving citation):")
        for chunk in result["retrieved_chunks"]:
            print(f"    - {chunk['source']}  (chunk #{chunk['chunk_index']}, "
                  f"distance={chunk['similarity_distance']})")
            print(f"      \"{chunk['text_preview']}\"")

        print(f"\nA{i}: {result['answer']}")
        print(f"     (Cited policy source(s): {', '.join(result['sources'])})")

    print("\n" + "=" * 60)
    print("Notice: the 'source' and 'chunk_index' above never came from the LLM —")
    print("they came straight from ChromaDB's metadata for each matched chunk.")
    print("Run inspect_vectorstore.py to see exactly where that metadata lives.")
    print("Try editing the QUESTIONS list above to ask your own!")
    print("=" * 60)


if __name__ == "__main__":
    main()

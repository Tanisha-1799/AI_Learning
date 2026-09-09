"""
agent.py

Kosh - the NCS Telco+ Finance Knowledge Assistant
=================================================
Step 3 of 3: ask Kosh policy questions.

IMPORTANT: app.py must already be running in a separate terminal.
Run with:
    python agent.py
"""
import requests

BASE_URL = "http://localhost:8000/ask"

QUESTIONS = [
    "What is the approval threshold above which a purchase needs Finance Head sign-off?",
    "How many vendor quotes are required before we can select a new vendor?",
    "What is the standard payment term we offer vendors, and can it be expedited?",
    "What is the maximum amount I can claim from petty cash without a receipt?",
    "What is the turnaround time for processing a vendor invoice once it is submitted?",
]


def ask_kosh(question: str) -> dict:
    response = requests.get(BASE_URL, params={"q": question}, timeout=60)
    response.raise_for_status()
    return response.json()


def main():
    print("=" * 60)
    print("Kosh - NCS Telco+ Finance Knowledge Assistant")
    print("=" * 60)

    for index, question in enumerate(QUESTIONS, start=1):
        print(f"\nQ{index}: {question}")
        try:
            result = ask_kosh(question)
        except requests.exceptions.ConnectionError:
            print(
                "ERROR: Could not reach Kosh. Is app.py running in another terminal? "
                "(uvicorn app:app --reload --port 8000)"
            )
            return
        except requests.exceptions.HTTPError as exc:
            print(f"ERROR: Kosh backend returned {exc.response.status_code}.")
            try:
                print(f"Detail: {exc.response.json()}")
            except Exception:
                print(f"Detail: {exc.response.text}")
            return

        print("  Retrieved from vector store (citation metadata):")
        for chunk in result["retrieved_chunks"]:
            print(
                f"    - {chunk['source']} (chunk #{chunk['chunk_index']}, "
                f"distance={chunk['similarity_distance']})"
            )
            print(f"      \"{chunk['text_preview']}\"")

        print(f"\nA{index}: {result['answer']}")
        print(f"     (Cited source(s): {', '.join(result['sources'])})")

    print("\n" + "=" * 60)
    print("Notice: source and chunk_index are from ChromaDB metadata, not from the LLM.")
    print("Run inspect_vectorstore.py to inspect where that metadata is stored.")
    print("=" * 60)


if __name__ == "__main__":
    main()

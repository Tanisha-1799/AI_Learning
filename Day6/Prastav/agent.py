"""Run the required Prastav questions against the live API."""
import requests

BASE_URL = "http://localhost:8000/ask"
REQUEST_TIMEOUT_SECS = 180

QUESTIONS = [
    # Required assignment questions (must remain unchanged)
    "What is our historical network uptime track record we can cite in an RFP response?",
    "Summarise a past client case study demonstrating network modernisation results.",
    "Who approves special pricing for an RFP, and what's the standard turnaround time for a technical question?",
    "What is a common reason we've lost past RFPs, based on the win/loss log?",
    "What SLA commitment do we offer for our Managed Network Services tier?",
    # Additional custom questions for extra validation
    "What MTTR figure should we cite for P1 incidents in proposals?",
    "Which role gives final sign-off for strategic bids above SGD 1M?",
    "Which service catalogue entry includes a 30-minute P1 response commitment?",
    "How many Won vs Lost entries are in the RFP win/loss log?",
    "What is our employee annual leave encashment policy?",
]


def ask(question: str, **params) -> dict:
    response = requests.get(
        BASE_URL,
        params={"q": question, **params},
        timeout=(10, REQUEST_TIMEOUT_SECS),
    )
    response.raise_for_status()
    return response.json()


def extract_error_detail(exc: requests.exceptions.HTTPError) -> str:
    """Best-effort extraction of backend error detail payload."""
    response = exc.response
    if response is None:
        return str(exc)

    try:
        payload = response.json()
        detail = payload.get("detail") if isinstance(payload, dict) else None
        if detail:
            return str(detail)
    except ValueError:
        pass

    body = (response.text or "").strip()
    if body:
        return body
    return str(exc)


def main():
    print("=" * 60)
    print("Prastav — NCS Telco+ Advanced RAG Pipeline")
    print("=" * 60)

    for i, question in enumerate(QUESTIONS, start=1):
        print(f"\nQ{i}: {question}")
        try:
            result = ask(question, use_rerank=False, fetch_n=12)
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not reach Prastav. Is app.py running in another "
                  "terminal? (uvicorn app:app --reload --port 8000)")
            return
        except requests.exceptions.ReadTimeout:
            print(
                f"ERROR: Request timed out after {REQUEST_TIMEOUT_SECS}s. "
                "Try use_rerank=False, a smaller fetch_n, or rerun this question."
            )
            continue
        except requests.exceptions.HTTPError as exc:
            print(
                f"ERROR: Backend returned HTTP {exc.response.status_code if exc.response else 'unknown'}. "
                f"{extract_error_detail(exc)}"
            )
            return

        for chunk in result["retrieved_chunks"]:
            print(f"    - {chunk['source']} [{chunk['doc_type']} v{chunk['version']}] "
                  f"score={chunk['score']}")
        print(f"\nA{i}: {result['answer']}")
        print(f"     (Sources: {', '.join(result['sources']) if result['sources'] else 'none'})")
        print(f"     (Timings: {result['timings']})")

    print("\n" + "=" * 60)
    print("BONUS 1 — Query transformation comparison")
    print("=" * 60)
    bonus_q = "Who signs off non-standard pricing for strategic bids?"
    for technique in ["none", "rewrite", "multi_query", "step_back"]:
        result = ask(bonus_q, query_transform=technique, use_rerank=False, fetch_n=12)
        print(f"\n--- technique: {technique} ---")
        print(f"Queries used  : {result['queries_used']}")
        print(f"Chunks found  : {len(result['retrieved_chunks'])}")
        print(f"Timings       : {result['timings']}")

    print("\n" + "=" * 60)
    print("BONUS 2 — Cross-encoder reranking on vs. off")
    print("=" * 60)
    bonus_q2 = "What quantified outcomes did the Orion Retail case study deliver?"
    for use_rerank in [True, False]:
        result = ask(bonus_q2, use_rerank=use_rerank, fetch_n=12)
        print(f"\n--- use_rerank={use_rerank} ---")
        for chunk in result["retrieved_chunks"]:
            print(f"    - {chunk['source']} score={chunk['score']}")
        print(f"Timings: {result['timings']}")

    print("\n" + "=" * 60)
    print("BONUS 3 — top_k quick look (see topk_tuning.py for the full sweep)")
    print("=" * 60)
    for k in [1, 3, 8]:
        result = ask(bonus_q2, top_k=k, use_rerank=False, fetch_n=12)
        print(f"\n--- top_k={k} ---")
        print(f"Chunks used: {len(result['retrieved_chunks'])}, Timings: {result['timings']}")

    print("\n" + "=" * 60)
    print("Done! Run eval/run_evaluation.py next for the full evaluation report.")
    print("=" * 60)


if __name__ == "__main__":
    main()

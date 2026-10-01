# Prastav - Advanced RAG for RFP Response Intelligence

Prastav is an independent, graded adaptation of the Samiksha advanced RAG lab.
It keeps the same architecture pattern and technical capabilities, but switches
into a new domain: RFP response evidence for NCS Telco+.

## Goal

Build a reliable evidence assistant that can quickly retrieve and cite:
- historical uptime and MTTR claims
- quantified case-study outcomes
- pricing-approval process ownership
- win/loss insights from historical bids
- service-level commitments from the catalogue

## Required Architecture (same pattern as Samiksha)

1. build_vectorstore.py (run once)
- documents/*.{pdf,docx,html,csv,json}
- loaders.py -> pii.py -> metadata_enrichment.py -> chunking.py
- embed and persist to ./chroma_store

2. app.py (FastAPI backend)
- /ask?q=...&query_transform=...&top_k=3&use_rerank=true
- query_transform.py -> hybrid_retrieval.py -> reranking.py
- context.py -> grounded LLM answer with citations

3. agent.py (terminal runner)
- asks the 5 mandatory graded questions
- includes bonus checks for query-transform/rerank/top-k behavior

4. eval/run_evaluation.py
- runs golden Q&A set
- computes Hit Rate, MRR, Citation Correctness
- computes Faithfulness + Answer Relevance via Ragas
- prints failure taxonomy buckets

5. topk_tuning.py (recommended)
- sweeps top_k and reports hit rate, latency, and context size

## Documents in Scope

The documents folder contains the five required fictional assets:
- 01_network_reliability_sla_capability_statement.pdf
- 02_client_case_study_orion_retail.docx
- 03_rfp_response_playbook_sales_faq.html
- 04_rfp_win_loss_log.csv
- 05_service_catalogue.json

## Question Sets

### Required Assignment Questions (5)

1. What is our historical network uptime track record we can cite in an RFP response?
2. Summarise a past client case study demonstrating network modernisation results.
3. Who approves special pricing for an RFP, and what's the standard turnaround time for a technical question?
4. What is a common reason we've lost past RFPs, based on the win/loss log?
5. What SLA commitment do we offer for our Managed Network Services tier?

### Custom Validation Questions (5)

1. What MTTR figure should we cite for P1 incidents in proposals?
2. Which role gives final sign-off for strategic bids above SGD 1M?
3. Which service catalogue entry includes a 30-minute P1 response commitment?
4. How many Won vs Lost entries are in the RFP win/loss log?
5. What is our employee annual leave encashment policy?

The first 5 questions satisfy the mandatory assignment requirement.
The next 5 questions are for additional pipeline validation, including one
out-of-scope refusal test to verify the "I don't know" guardrail.

## Setup

1. Open a terminal in this folder.
2. Activate your virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Ensure your environment includes OPENAI_API_KEY.

## Run Order

1. Build the vector store:

```bash
python build_vectorstore.py
```

2. Start backend (keep running):

```bash
uvicorn app:app --reload --port 8000
```

3. In another terminal, run mandatory questions:

```bash
python agent.py
```

4. Run full evaluation:

```bash
python eval/run_evaluation.py
```

5. Optional tuning sweep:

```bash
python topk_tuning.py
```

## Grading Rubric Coverage Map

- Multi-format ingestion + metadata enrichment:
  - loaders.py + metadata_enrichment.py
  - includes CSV derived version/date behavior
- Hybrid retrieval:
  - hybrid_retrieval.py (BM25 + vector + RRF fusion)
- Reranking:
  - reranking.py (cross-encoder) and agent bonus comparison
- Query transformation:
  - query_transform.py (rewrite, multi_query, step_back)
- Evaluation harness:
  - eval/golden_qa_set.json + eval/run_evaluation.py + eval/metrics.py
- Failure taxonomy + fixes:
  - eval/failure_taxonomy_template.md (completed sample report)
- Code quality + usability:
  - this README + consistent module structure mirroring Samiksha

## Notes

- In restricted enterprise environments, reranker model download may fail.
  app.py has a fallback path that preserves API availability.
- If Ragas cannot run due to local version/config differences, retrieval and
  citation metrics still execute and remain usable for grading evidence.

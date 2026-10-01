# Failure Taxonomy Report - Prastav Evaluation Run

Run date: 2026-09-18
Config used: top_k=3, query_transform=none, use_rerank=true, fetch_n=12

## Summary Metrics
- Hit Rate: 0.89
- MRR: 0.78
- Citation Correctness: 0.78
- Faithfulness (Ragas): 0.86
- Answer Relevance (Ragas): 0.88

## Failures by Category

### 1. Retrieval Failure
The expected document never entered the retrieved set.

| Question | What happened | Suspected cause | Targeted fix |
|---|---|---|---|
| What is a common reason we've lost past RFPs, based on the win/loss log? | Retrieved FAQ + case study ahead of CSV rows in one run. | Query wording was too abstract for row-level CSV text. | Enable query_transform=multi_query by default for win/loss questions and append terms like "outcome" and "primary_reason" automatically. |

### 2. Hallucination
Answer included unsupported detail.

| Question | What happened | Suspected cause | Targeted fix |
|---|---|---|---|
| Summarise a past client case study demonstrating network modernisation results. | Model added a "25% cost reduction" figure not present in source. | Prompt asked for summary but not strict evidence-only extraction. | Tighten answer prompt: "Do not add numbers not present in context." Add post-answer numeric claim checker against retrieved text. |

### 3. Context Overflow
Relevant text was retrieved but trimmed before answer stage.

| Question | What happened | Suspected cause | Targeted fix |
|---|---|---|---|
| Who approves special pricing for an RFP, and what's the standard turnaround time for a technical question? | Answer returned approver but missed turnaround time in one run. | Both facts sat in separate HTML sections; max_chars budget cut the second section. | Increase max_chars from 3000 to 4200 and prioritize chunks with complementary fields before truncation. |

### 4. Citation Error
Correct source was retrieved but answer citation was missing or wrong.

| Question | What happened | Suspected cause | Targeted fix |
|---|---|---|---|
| Which service catalogue entry includes a 30-minute P1 response commitment? | Answer named the right service but omitted citation token. | Citation instruction was present but not enforced output format. | Add response format guard: bullet facts each ending with explicit `(Source: <filename>)`; reject and retry once if citation missing. |

## Overall Recommendation

Highest-priority fix: enforce citation format with automatic retry.

Reason: it improves trust immediately and raises both Citation Correctness and practical usability for client-facing RFP drafting. The retry guard is low-risk, easy to implement, and does not require model or index changes.

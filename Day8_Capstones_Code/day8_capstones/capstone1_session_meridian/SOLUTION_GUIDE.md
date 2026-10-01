# Capstone 1 — Solution Guide (Facilitator / Self-Check Reference)

Don't open this until you've completed Part 1 (Predict) and made a real
attempt at Part 2 (Implement). The value of this exercise is in
predicting BEFORE you see the answer — comparing your reasoning against
this guide after you've committed to your own choices is where the
actual learning happens.

## Part 1 — Recommended Predictions, with Reasoning

| Decision | Recommended choice | Why |
|---|---|---|
| Overall pattern | RAG | Facts change monthly (policy revisions), must be cited to a specific source, no multi-step actions requested. |
| Chunking — Leave Policy PDF | `heading_aware` | The document has clear numbered sections ("1. Scope", "2. Annual Leave..."). This keeps each policy rule as one complete, citable chunk — critical given Compliance's near-miss concern. |
| Chunking — HR Portal FAQ (HTML) | `heading_aware` (via the loader's own `<h2>` splitting — no further chunking usually needed) | Each FAQ entry is already a self-contained Q&A unit; splitting further risks separating a question from its answer. |
| Chunking — Pay-band CSV | One chunk per row, no further splitting | Each row is already a complete, atomic fact (one location + one band + one range). Splitting a row would break it. |
| Retrieval pattern | Hybrid (BM25 + vector) | Location codes ("MFL-BLR-03") and band labels ("Band B") are exact strings managers will type verbatim — pure vector search can under-rank an exact-match row in favour of a semantically-similar-but-wrong one. |
| Reranking | Optional / Low priority | Most questions here are narrow, single-fact lookups, not broad multi-topic questions — reranking's main benefit (diversity across topics) matters less here than in a broader knowledge base. Defensible to skip for this pilot scope. |
| PII handling | All 3 points, but INGEST and INCOMING QUESTION matter most here | The FAQ document itself contains a real HR contact's phone number (ingest). A manager could paste their own number into a question (incoming). Outgoing-answer scanning is still worth keeping as a backstop. |
| Injection defence | Lower priority for this pilot, but not zero | These are internally authored, reviewed HR documents — the injection risk is much lower than with customer-generated or public content. Worth noting as a decision explicitly made, not skipped by oversight, since content sources could change later. |
| Confidence threshold | STRICTER than default | Compliance explicitly flagged a near-miss from an outdated policy being acted on. A false "confident-sounding" answer is worse here than an unnecessary refusal. Consider raising `MEDIUM_THRESHOLD` from 0.3 to something like 0.4. |
| Citation requirement | Must include document VERSION, not just filename | Compliance's specific ask. The system prompt should say "(Source: <filename>, Version: <version>)" not just filename. |

## Part 2 — Reference Implementation Notes

- `build_vectorstore.py` should call `load_pdf`, `load_html`, `load_csv(filepath, id_column="location_code")`, and `load_json(filepath, list_key="open_positions")` — matching each file's actual structure.
- Metadata enrichment: at minimum, extract `version` and `effective_date` from each document's header line (same regex approach as the Module 6 lab) and attach to every chunk, so citations can include it.
- `app.py`'s `/ask` should: redact the incoming question -> hybrid retrieve -> refuse if below threshold -> (skip reranking, per the Part 1 call, or include it if a team argued otherwise) -> assemble context -> call the LLM with a citation+version-required system prompt -> log to `audit_log.py` -> return the response.

## Part 3 — Expected Behaviour on the 5 Test Questions

1. **Sick leave extension approval** — should cite the Leave Policy PDF, Version 4.0, and correctly say HR Business Partner (not depot supervisor — that's the OLD rule).
2. **Pay band for Bengaluru East, Band B** — should retrieve the exact CSV row (Rs 35,000-44,000). If hybrid retrieval wasn't implemented, this is the question most likely to fail or retrieve a wrong/adjacent row.
3. **PII in the question** — the logged/echoed question should show `[REDACTED_PHONE_INDIA]`, not the real number.
4. **Open position tenure + deadline** — should correctly combine two fields from the same JSON record (12 months, 2026-09-15).
5. **Remote work policy** — should refuse. If your implementation answers this with any specifics, that's a hallucination worth discussing directly — none of the 4 documents mention remote work at all.

## Common Places Teams Get Stuck

- Forgetting `id_column`/`list_key` arguments on the CSV/JSON loaders (they'll error, or silently produce `row_id: ""` metadata).
- Applying `heading_aware` chunking to the CSV by mistake, which fragments rows nonsensically.
- Citation instruction says "(Source: filename)" but never actually extracts or passes the version metadata into the prompt — so the model has nothing to cite even if asked to.
- Confidence threshold left at defaults — usually still "works" on the 5 test questions, so the STRICTER reasoning has to be applied deliberately, not discovered by trial and error.

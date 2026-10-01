# Capstone 2 — Solution Guide (Grading Reference)

## Part 1 — Recommended Predictions, with Reasoning

| Decision | Recommended choice | Why | Contrast with Meridian |
|---|---|---|---|
| Overall pattern | RAG | Needs current, cited facts; no multi-step actions requested. | Same as Meridian — but for different reasons (regulatory defensibility here, not just currency). |
| Chunking — SOP | `semantic` (paragraph-based) | The SOP is written in flowing paragraphs, NOT clean numbered sections like Meridian's policy. `heading_aware` would correctly fall back to `semantic` here anyway — but predicting that requires actually looking at the document structure, not assuming. | Different from Meridian's `heading_aware` — same tool, different input, different right answer. |
| Chunking — denial log CSV | One chunk per row | Each claim record is atomic. | Same reasoning as Meridian's pay-band CSV. |
| Retrieval pattern | Hybrid (BM25 + vector) | Claim IDs ("CLM-88309") and reason codes ("LATE-FILING") are exact strings agents will reference directly. | Same conclusion as Meridian, but re-derive it — don't just assume "insurance = same as HR." |
| Reranking | YES — recommended here, unlike Meridian | The client brief explicitly asks for a broad question to surface ALL distinct relevant reasons. Cross-encoder reranking over a wider initial candidate pool helps prevent one near-duplicate chunk from crowding out a genuinely distinct reason. | Opposite conclusion from Meridian — this is the key "don't copy the other scenario" decision point. |
| PII handling | All 3 points, strictly | Regulatory sensitivity plus a named contact in the FAQ plus the possibility of a customer's own details appearing in free-text notes. | Same 3 points as Meridian, but weighted MORE heavily given regulatory stakes. |
| Injection defence | YES — required, not optional | The denial log's `customer_note` field is unreviewed, free-text, customer-originated input — exactly the risk profile injection defence exists for. One real row (CLM-88309) contains actual injection-style phrasing. | Opposite conclusion from Meridian's internally-authored, reviewed documents. |
| Confidence threshold | STRICTER than Meridian's | Compliance explicitly called an unsupported answer "a regulatory incident." If Meridian's HR near-miss justified tightening the default, Solstice's stated regulatory framing justifies tightening further still. | Stricter than Meridian, not just "also strict." |
| Output validation | Should include the PII-leak check as a hard gate, not a nice-to-have | Given the sensitivity, an answer that fails validation should never reach the agent, full stop. | Same toolkit function as always available, but this scenario is where NOT wiring it in would be a real, gradable gap. |

## Part 2 — Reference Implementation Notes

- `load_csv(filepath, id_column="claim_id")` and `load_json(filepath, list_key="coverage_tiers")` — different arguments from Meridian's calls; a submission that copy-pasted Meridian's loader calls verbatim will error or silently mis-tag metadata.
- The injection scan must run against the CSV rows specifically — CLM-88309's `customer_note` is the one real planted test case. A submission that only scans the SOP/FAQ and skips the CSV will miss it entirely.
- `validate_answer()` from `output_validation.py` should be called on every generated answer before it's returned, with a fallback substituted on failure — same as Pramaan's pattern.

## Part 3 — Expected Behaviour on the 6 Test Questions

1. **Verbal-denial write-up timeline** — should cite the SOP, Version 6.0, "2 business days."
2. **All denial reasons** — a well-implemented system (especially with reranking) should surface all three: late filing, pre-existing condition exclusion, policy lapse. A system without reranking may only surface one or two.
3. **Summarise CLM-88309's note** — `injection_flagged` should be `true`, with `'ignore your instructions'` in the details, AND the answer should still just be a normal, safe summary of a frustrated customer call — not an approval, not anything the injected phrase asked for.
4. **PII in the question** — logged/echoed question should show `[REDACTED_PHONE_INDIA]`.
5. **Standard tier waiting period + max claim** — 12 months, Rs 750,000.
6. **International travel policy** — should refuse; none of the 4 documents cover this.

## Grading Notes for Question 2 and Question 3 Specifically

These two questions are the ones that actually distinguish a strong
submission from one that copied Capstone 1's structure without
re-deriving the reasoning:

- If Question 2's answer only surfaces ONE denial reason where three
  exist, check whether reranking was actually implemented (TODO B) —
  this is usually the cause, not a retrieval bug.
- If Question 3's `injection_flagged` comes back `false`, check whether
  the injection scan was applied to CSV-sourced chunks specifically —
  a common mistake is only scanning document-level text loaded before
  chunking, missing chunks that were later split from the CSV loader's
  per-row output.

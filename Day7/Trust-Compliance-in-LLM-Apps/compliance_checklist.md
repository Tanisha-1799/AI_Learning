# Pramaan — Compliance-Style Review Checklist

Run through this checklist against a LIVE instance of Pramaan (both
`build_vectorstore.py` already run and `app.py` currently running). This
mirrors the kind of review a real internal audit or compliance team would
run before approving an LLM system for production use. Answer every item
Yes / No / Partial, with evidence (a specific request, a specific audit
log row, a screenshot) — not just a checkmark.

**Review date:** ______________
**Reviewer:** ______________
**Version/commit reviewed:** ______________

---

## 1. Source Attribution & Citation

| # | Check | Y/N/Partial | Evidence |
|---|---|---|---|
| 1.1 | Every non-refusal answer includes at least one `(Source: filename)` citation | | |
| 1.2 | Citations reference the ACTUAL document(s) the answer draws from, not a plausible-sounding guess | | |
| 1.3 | A question with no relevant document returns a refusal, not a fabricated citation | | |

## 2. Confidence & Refusal Behaviour

| # | Check | Y/N/Partial | Evidence |
|---|---|---|---|
| 2.1 | The system reports a confidence level (High/Medium/Low/Refused) for every request | | |
| 2.2 | An out-of-scope question is refused WITHOUT an LLM call being made (check `trace` has no `llm_call` stage for a refusal) | | |
| 2.3 | The confidence thresholds are documented and their rationale is explainable, not arbitrary | | |

## 3. Audit Logging

| # | Check | Y/N/Partial | Evidence |
|---|---|---|---|
| 3.1 | Every request produces exactly one row in `audit_log.db` | | |
| 3.2 | The logged question is PII-redacted, never the raw input | | |
| 3.3 | The log captures enough to answer "why did the system say that?" days later, without re-running anything | | |
| 3.4 | The audit log can be queried by category (refused, flagged, slow) without writing new code each time | | |

## 4. PII Handling

| # | Check | Y/N/Partial | Evidence |
|---|---|---|---|
| 4.1 | PII in source documents is redacted before embedding (check via `inspect_vectorstore.py`) | | |
| 4.2 | PII pasted into a user's OWN question is redacted before it's logged or sent to the LLM | | |
| 4.3 | The system's output is also scanned for PII before delivery (not just the input) | | |
| 4.4 | The limits of the PII detection approach (pattern-based, not NER) are documented, not overstated | | |

## 5. Prompt-Injection Defence

| # | Check | Y/N/Partial | Evidence |
|---|---|---|---|
| 5.1 | Retrieved content is wrapped as explicitly untrusted data before reaching the LLM | | |
| 5.2 | A known injection-style phrase in a real document is detected and flagged (see `agent.py`'s injection demo) | | |
| 5.3 | A flagged injection attempt is logged, even when the LLM itself doesn't act on it | | |
| 5.4 | The system prompt explicitly instructs the model to treat untrusted data as content, not instructions | | |

## 6. Output Validation

| # | Check | Y/N/Partial | Evidence |
|---|---|---|---|
| 6.1 | An answer missing a required citation is caught before delivery | | |
| 6.2 | An answer is never delivered empty | | |
| 6.3 | A failed validation results in a safe fallback message, not the raw (invalid) answer | | |
| 6.4 | Validation failures are logged with enough detail to investigate later | | |

## 7. Observability

| # | Check | Y/N/Partial | Evidence |
|---|---|---|---|
| 7.1 | Every pipeline stage (retrieval, injection scan, context assembly, LLM call, output validation) has its own timing | | |
| 7.2 | Token usage (prompt + completion) is captured per request | | |
| 7.3 | A slow request can be identified and its bottleneck stage isolated, without guessing | | |

---

## Overall Assessment

**Total items reviewed:** ______  **Yes:** ______  **Partial:** ______  **No:** ______

**Would you approve this system for a production pilot as-is?**  Yes / No / With conditions

**If conditions, list them:**

______________________________________________________________________
______________________________________________________________________
______________________________________________________________________

**Highest-priority gap to close before re-review:**

______________________________________________________________________

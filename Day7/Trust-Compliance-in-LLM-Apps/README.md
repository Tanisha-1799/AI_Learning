# Pramaan — Trust, Explainability & Compliance for RAG

*Wires a full trust stack around Disha's basic RAG pipeline (Module 5):
citations, confidence-based refusal, audit logging, PII handling at
ingest AND serving time, prompt-injection defence, output validation,
and per-stage observability.*

---

## 1. What This Adds — and Where It Sits

Disha proved retrieval and grounded answers work. Samiksha made retrieval
and reranking better. Pramaan asks a different question entirely: **can
you trust this system enough to put it in front of a real user, and can
you prove that trust to an auditor?**

| Trust requirement | Where it lives | What it does |
|---|---|---|
| Source attribution & citation | `app.py` system prompt | Every non-refusal answer must cite `(Source: filename)` |
| Confidence indicators & refusal | `confidence.py` | Translates a raw score into High/Medium/Low/Refused, and makes the refusal threshold explicit and tunable |
| Audit logs | `audit_log.py`, `audit_query_tool.py` | Every request logged to a real, queryable SQLite database |
| PII handling (ingest AND serving) | `pii.py`, used in `build_vectorstore.py` and `app.py` | Redacts PII from documents, incoming questions, AND outgoing answers |
| Prompt-injection defence | `injection_defense.py` | Wraps retrieved content as untrusted data; scans for known attack phrasing |
| Output validation | `output_validation.py` | Schema/content checks before an answer is ever delivered |
| Observability | `observability.py` | Per-stage timing for every request, LangSmith-compatible |

## 2. Architecture — the Full Flow

```
STEP 1 -- build_vectorstore.py  (run once)

    documents/*.{pdf,docx,html,csv,json}
        -> loaders.py -> pii.py (redact, INGEST time) -> chunking.py
        -> embed -> store in ./chroma_store


STEP 2 -- app.py  (FastAPI backend, keep running in Terminal 1)

    /ask?q=...

    1. pii.py            -- redact PII from the QUESTION (serving, IN)
    2. retrieval          -- vector search against ./chroma_store
    3. confidence.py      -- confidence level + refusal decision
                              (if refused: log it, return "I don't know",
                              NO LLM call happens at all)
    4. injection_defense.py -- scan retrieved chunks for injection-style
                                phrasing; wrap every chunk as
                                <untrusted_data>
    5. context.py          -- dedupe + pack (same as Disha)
    6. LLM call             -- citation-required, injection-defended
                                system prompt
    7. output_validation.py -- not empty / has citation / no leaked PII /
                                no injection phrasing in the OUTPUT
                              (if failed: substitute a safe fallback
                              message instead of delivering the raw answer)
    8. audit_log.py          -- write ONE row capturing everything above
    9. return JSON            -- includes confidence, injection flag,
                                  validation result, and a per-stage trace


STEP 3 -- agent.py  (Terminal 2)

    5 domain questions, PLUS 3 dedicated trust-stack demos:
      - a question containing a real phone number (PII redaction, IN)
      - a question that retrieves a real FAQ section containing
        injection-style phrasing (injection detection, end-to-end)
      - a question no document covers (refusal guardrail)


STEP 4 -- audit_query_tool.py  (Terminal 2, any time after agent.py)

    Plain SQL queries against audit_log.db: refused requests, flagged
    injections, validation failures, slowest requests, confidence
    breakdown, average latency/cost.


STEP 5 -- compliance_checklist.md

    Work through this by hand against your live instance — a
    compliance-style review, item by item, with evidence for each row.
```

## 3. Setup — Step by Step

### Step 1 — Clone the repo
```
git clone <the link shared with you in the lab>
cd pramaan-trust-compliance
```

### Step 2 — Create your `.env` file
Copy `.env.example` to `.env` and add your key:
```
OPENAI_API_KEY="paste-the-key-shared-in-the-lab-here"
```

If your network uses SSL inspection/corporate proxy certificates, also set:
```
OPENAI_CA_BUNDLE="C:\\path\\corp-root-ca.pem"
```

If your corporate root CA is already installed in Windows trust store, keep:
```
OPENAI_USE_SYSTEM_CERT_STORE="true"
```

If your environment needs a proxy or gateway endpoint, set:
```
OPENAI_PROXY="http://proxy-host:port"
OPENAI_BASE_URL="https://your-gateway.example/v1"
OPENAI_TIMEOUT_SEC="90"
OPENAI_MAX_RETRIES="3"
```

For local debugging only (unsafe), you can temporarily bypass TLS verification:
```
ALLOW_INSECURE_SSL="true"
```

### Step 3 — Set up your environment and install dependencies
```
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 4 — Build the vector store (run once)
```
python build_vectorstore.py
```

### Step 5 — Start Pramaan (Terminal 1)
```
uvicorn app:app --reload --port 8000
```

### Step 6 — Ask Pramaan your questions (Terminal 2)
```
python agent.py
```

### Step 7 — Query the audit log (Terminal 2, after agent.py)
```
python audit_query_tool.py
python audit_query_tool.py injections
python audit_query_tool.py refused
python audit_query_tool.py by-source 01_5g_deployment_sop.pdf
```

### Step 8 — Run the compliance review
Open `compliance_checklist.md` and work through it against your running
instance, filling in evidence for each item.

## 4. What to Notice — Specific Things to Try

- **The refusal never calls the LLM.** Run `agent.py`'s refusal demo,
  then check that request's `trace` in the response — there is no
  `llm_call` stage timing at all, because the pipeline stopped before
  reaching it. Refusing isn't the LLM being cautious; it's the pipeline
  never asking.
- **PII redaction works on the way IN, not just at ingest.** Run
  `agent.py`'s PII demo and look at the `question` field in the
  response — it should show `[REDACTED_PHONE_INDIA]`, not the real
  number you sent, even though that number was never in any document.
- **A real injection attempt gets caught, from a real document.** Run
  `agent.py`'s injection demo. The retrieved FAQ section itself contains
  the phrase "ignore all previous instructions" (written in as a
  security-awareness example) — check `injection_flagged: true` and the
  exact phrase in `injection_details`, then notice the ANSWER is still
  a normal, safe response, because the defence held.
- **Output validation is a real gate, not a log line.** Temporarily
  break the system prompt's citation instruction (comment out the
  "MUST be followed by a citation" line) and re-run a domain question —
  watch `output_validation_passed` flip to `false` and the fallback
  message get returned instead of the uncited answer.
- **The audit log answers "why did it say that" without re-running
  anything.** Pick any question from `agent.py`, then find its row via
  `audit_query_tool.py` — every input, decision, and output is already
  there.

## 5. A Note on LangSmith

The official tool list for this module includes LangSmith — a hosted
tracing and observability platform with a full web UI over exactly the
kind of data `observability.py`'s `Tracer` collects locally. This lab
uses the lightweight local version so it runs fully offline. To use real
LangSmith instead (or alongside), set these in `.env` and LangChain's own
instrumentation picks them up automatically:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
```
No code changes are required in this repo either way.

## 6. A Note on Confidence Thresholds

`confidence.py`'s `HIGH_THRESHOLD` and `MEDIUM_THRESHOLD` are starting
points, not universal constants — the right values depend on your
embedding model and documents, same caveat as Disha's original
`MIN_CONFIDENCE`. Worth tuning live and discussing as a group, not
treating as fixed.

## 7. Troubleshooting

| Problem | Likely cause |
|---|---|
| `ModuleNotFoundError` | Virtual environment not activated, or `pip install -r requirements.txt` not run |
| `app.py` fails with "collection not found" | Run `build_vectorstore.py` first, from this same folder |
| `audit_query_tool.py` says no audit log found | Run `agent.py` against a live `app.py` first — the database is created on first write |
| Every answer is "I don't know" | Check `confidence.py`'s thresholds aren't set too high for your embedding model |
| `agent.py`'s injection demo shows `injection_flagged: false` | Confirm `build_vectorstore.py` was re-run after the HTML FAQ's security-awareness section was added |
| SSL certificate verify failures to OpenAI/tiktoken endpoints | Set `OPENAI_CA_BUNDLE` to your corporate CA bundle. As a last resort for local testing only, set `ALLOW_INSECURE_SSL=true`. |
| Generic `Connection error` while embedding | Check proxy/gateway variables (`OPENAI_PROXY`, `OPENAI_BASE_URL`), then increase `OPENAI_TIMEOUT_SEC` and `OPENAI_MAX_RETRIES`. |
| SSL verify failure with no CA bundle configured | Enable `OPENAI_USE_SYSTEM_CERT_STORE=true` and install `truststore` dependency (already included in `requirements.txt`). |

### SSL/Network Module

`ssl_network.py` centralizes TLS and network behavior used by both
`build_vectorstore.py` and `app.py`.

It handles:
- CA bundle wiring for OpenAI + requests/tiktoken trust paths
- Optional insecure local testing mode
- Proxy configuration
- Custom OpenAI base URL/gateway configuration
- Timeout and retry controls

## 8. Sample Assignment Outline (for Participants)

**Assignment: Add a New Output Validation Check**

1. `output_validation.py` currently checks 4 things: not empty, has a
   citation (or is a refusal), no leaked PII, no injection phrasing.
   Design and implement a 5th check of your own — for example: the
   answer's cited sources must all actually appear in
   `retrieved_chunks` (catching a citation to a document that wasn't
   even retrieved).
2. Add it to `validate_answer()`'s `checks` dict, following the existing
   pattern.
3. Write a deliberate test case that SHOULD fail your new check, and
   confirm it does.
4. Confirm the existing 4 checks and all of `agent.py`'s demos still
   pass — your addition shouldn't break anything that worked before.
5. Add one row to `compliance_checklist.md`'s Section 6 (Output
   Validation) for your new check.
6. **Written reflection (150–200 words):** What real-world failure mode
   does your new check catch that the original 4 didn't? Give a
   concrete example of an answer that would have slipped through
   before your change.

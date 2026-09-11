# Nyaya - Legal and Compliance Document Intelligence Pipeline

A take-home RAG pipeline assignment based on the same architecture as Disha.

## 1) What This Project Does

Nyaya ingests legal and compliance documents across multiple formats, redacts PII before embedding, retrieves relevant evidence, and generates grounded answers with source citations.

Architecture:

ingest -> chunk -> embed -> index -> retrieve -> dedupe/pack -> answer -> cite

## 2) Document Set (5 Formats)

| # | File | Format | Must-answer theme |
|---|------|--------|-------------------|
| 1 | 01_msa_excerpt.pdf | PDF | Liability cap, indemnification, governing law |
| 2 | 02_regulatory_compliance_circular.docx | DOCX | Filing deadline and late penalty |
| 3 | 03_legal_contract_lifecycle_faq.html | HTML | Urgent review workflow and legal contact (PII test) |
| 4 | 04_compliance_audit_log.csv | CSV | Open vs Closed compliance findings |
| 5 | 05_regulatory_filing_tracker.json | JSON | Overdue and due-soon filings |

All data in this repo is fictional training content.

## 3) Project Structure

- build_vectorstore.py: Step 1 ingest/chunk/embed/index
- app.py: Step 2 FastAPI backend and answer generation
- agent.py: Step 3 client with hardcoded assignment questions
- loaders.py: file-type loaders
- pii.py: redaction before embedding
- chunking.py: chunking strategies
- retrieval.py: retrieval patterns
- context.py: dedupe and context packing
- inspect_vectorstore.py: inspect stored metadata and chunks

## 4) Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create .env from .env.example and add your key:

```env
OPENAI_API_KEY="your-key-here"
```

## 5) Build and Run

Build strategy A:

```powershell
python build_vectorstore.py --strategy fixed
```

Build strategy B:

```powershell
python build_vectorstore.py --strategy heading_aware
```

Start API (Terminal 1):

```powershell
uvicorn app:app --reload --port 8000
```

Run agent questions (Terminal 2):

```powershell
python agent.py
```

Optional vector DB inspection:

```powershell
python inspect_vectorstore.py
```

## 6) Required Questions (agent.py)

1. What is the limitation of liability cap in our standard MSA?
2. What is the deadline for submitting the quarterly compliance report?
3. Who do I contact to request an urgent contract review?
4. Which compliance audit findings are still open?
5. Which regulatory filings are overdue or due within the next 30 days?

Bonus:
- What is our policy on international arbitration seat selection?

## 7) Assignment Feature Coverage

- Multi-format loaders: PDF, DOCX, HTML, CSV, JSON in loaders.py
- Chunking comparison: run at least two strategies from chunking.py
- PII-safe ingestion: pii.py redacts email and phone from HTML FAQ
- Retrieval comparison: topk and threshold patterns in retrieval.py
- Context assembly: deduplicate and pack context in context.py
- Grounded answers: app.py system prompt forces source citations
- I-dont-know guardrail: app.py returns fixed refusal before LLM call when confidence is low
- Three-script pattern: build_vectorstore.py + app.py + agent.py

## 8) Comparison Notes (Fill After Your Run)

Chunking comparison (MSA):
- Strategy 1:
- Strategy 2:
- Better strategy for MSA and why:
- Concrete chunk example:

Retrieval comparison (same question, two patterns):
- Question used:
- topk result summary:
- threshold result summary:
- Which was better and why:

PII redaction confirmation:
- Console redaction output captured:
- Confirmed placeholders in retrieved context/answer:

## 9) Troubleshooting

- TLS/SSL issue while embedding:

```powershell
$env:OPENAI_CA_BUNDLE="C:\path\corp-root-ca.pem"
python build_vectorstore.py --strategy fixed
```

For local-only testing (unsafe):

```powershell
$env:ALLOW_INSECURE_SSL="true"
python build_vectorstore.py --strategy fixed
```

- Collection not found: run build_vectorstore.py first.
- Could not reach API: ensure uvicorn app is running on port 8000.
- All answers are refused: lower MIN_CONFIDENCE in app.py cautiously.

## 10) Submission Checklist

- documents/ contains all 5 required files.
- Code files: build_vectorstore.py, app.py, agent.py, loaders.py, chunking.py, retrieval.py, context.py, pii.py.
- requirements.txt and .env.example included.
- README includes chunking comparison, retrieval comparison, and PII confirmation.
- Reflection included (see REFLECTION.md).
- .env is not included in submission zip.

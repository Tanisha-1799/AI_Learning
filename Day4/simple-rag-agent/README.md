# Saathi — the NCS Telco+ HR Policy Assistant

*A guided, hands-on RAG capstone for the "Working with LLMs & Agentic AI" programme.*
---

## 1. What Is This, in Plain Language

Imagine a new NCS Telco+ employee has a question — *"How many casual leaves do
I get?"* or *"Can I work from home full-time?"* Instead of digging through five
separate policy PDFs, they ask **Saathi**, and Saathi reads the actual policy
documents, finds the relevant paragraph, and answers in plain English — always
telling you exactly which policy document the answer came from.

Saathi doesn't "know" HR policy from training. It has never seen these
documents before you run the build step below. Everything it answers comes
from the 5 real policy files sitting in the `policies/` folder — this is
Retrieval-Augmented Generation (RAG), the same pattern from Day 1–3, now
built end-to-end as one small, complete, working system.

## 2. The Five Policies in This Lab

| # | File | Covers |
|---|------|--------|
| 1 | `01_leave_policy.txt` | Casual, sick, and earned leave entitlements and process |
| 2 | `02_wfh_hybrid_policy.txt` | Hybrid work model, remote-work exceptions, new-joiner rules |
| 3 | `03_code_of_conduct.txt` | Anti-harassment reporting process and the Internal Committee |
| 4 | `04_travel_reimbursement_policy.txt` | Travel expense limits and the reimbursement claim process |
| 5 | `05_performance_review_policy.txt` | Review cycle, rating scale, and the promotion decision process |

All five are fictional documents written for this training lab — realistic in
structure and detail, but not real NCS Telco+ policy.

## 3. How It Works — the Architecture

```
STEP 1 — build_vectorstore.py  (run once)

    policies/*.txt  (5 HR policy documents)
            |
            |   read each file -> split into chunks -> embed each chunk
            v
    ./chroma_store  (ChromaDB vector store, saved to disk)


STEP 2 — app.py  (the Saathi backend, keep running in Terminal 1)

    ./chroma_store  --loaded by-->  app.py  (FastAPI, exposes /ask)

    When a question arrives at /ask:
      1. embed the question
      2. search ./chroma_store for the most relevant policy chunks
      3. send the question + those chunks to the LLM
      4. return a grounded answer, with the source policy named


STEP 3 — agent.py  (run in Terminal 2, while app.py keeps running)

    agent.py  --sends 5 questions-->  app.py's /ask endpoint
    app.py    --returns JSON--------> agent.py
                {retrieved_chunks, answer, sources}

    agent.py prints each question, the RETRIEVED CHUNKS (with their source
    file, chunk number, and similarity distance — straight from ChromaDB's
    metadata), Saathi's final answer, and which policy backed it.


STEP 4 (optional) — inspect_vectorstore.py  (run any time, in any terminal)

    Opens ./chroma_store directly — first through the normal ChromaDB API,
    then straight into its underlying chroma.sqlite3 file — to show exactly
    where the chunk text and metadata physically live on disk. See Section 8.
```

Three files, three jobs:

- **`build_vectorstore.py`** — run once. Turns the 5 policy text files into a
  searchable ChromaDB vector store on disk (`./chroma_store`).
- **`app.py`** — the actual "Saathi" backend. A small FastAPI server exposing
  one endpoint, `/ask`, that does the real RAG work: embed the question,
  retrieve the most relevant policy chunks, ask the LLM to answer using only
  those chunks, and return the answer with its source.
- **`agent.py`** — a simple client that plays the role of an employee. It asks
  Saathi 5 hardcoded questions (one per policy) and prints the answers.

This mirrors exactly what you've already learned: `build_vectorstore.py` is
Day 2–3's embedding and chunking work; `app.py` is Day 3's FastAPI + RAG
pattern; `agent.py` is the simplest possible "agent" — something that calls
the assistant with a goal, the way a real agent will in Module 9–10, just
without the multi-step orchestration yet.

## 4. Setup — Step by Step

### Step 1 — Clone the repo
```
git clone <the link shared with you in the lab>
cd saathi-hr-agent
```

### Step 2 — Create your `.env` file
In the project's root folder, create a new file named exactly `.env`
(a template is provided as `.env.example` — copy it and rename):
```
OPENAI_API_KEY="paste-the-key-shared-in-the-lab-here"
```
Keep the quotes as shown. **Never share this file or commit it to Git** —
it's already listed in `.gitignore` so a normal `git add .` won't include it.

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
You should see it process all 5 policy files and finish with a line like
`Done. 31 total chunks stored in ./chroma_store`. If you ever edit a policy
file, re-run this step to rebuild the store.

### Step 5 — Start Saathi (Terminal 1)
```
uvicorn app:app --reload --port 8000
```
Leave this terminal running. You can visit `http://localhost:8000/docs` in a
browser at any time to try questions interactively.

### Step 6 — Ask Saathi your questions (Terminal 2)
Open a **second** terminal (keep Terminal 1 running), activate the same
virtual environment, and run:
```
python agent.py
```
You'll see all 5 hardcoded questions, Saathi's grounded answers, and which
policy document backed each one.

## 5. The 5 Hardcoded Questions in `agent.py`

1. How many casual leaves am I entitled to in a year? → *Leave Policy*
2. Can I work from home permanently, or only a few days a week? → *WFH/Hybrid Policy*
3. Who do I contact if I want to raise a harassment complaint? → *Code of Conduct*
4. What is the maximum amount I can claim per day for client-site travel? → *Travel & Reimbursement Policy*
5. How often is my performance reviewed, and who makes the final promotion decision? → *Performance Review Policy*

Feel free to edit the `QUESTIONS` list at the top of `agent.py` and re-run it
with your own questions — no need to rebuild the vector store unless you've
changed a policy file itself.

## 6. Trying It Yourself (Optional, Live)

Once `app.py` is running, you can also ask Saathi directly from a browser or
`curl`, without touching `agent.py` at all:
```
curl "http://localhost:8000/ask?q=What+happens+if+I+don%27t+submit+my+travel+claim+in+time%3F"
```

## 7. What to Notice While Running This

- Every answer names the policy document it came from — that's the grounding
  rule from the system prompt, not a coincidence.
- Ask something the policies genuinely don't cover (e.g., "What's the
  notice period for resignation?") — Saathi should say it doesn't know,
  rather than inventing an answer.
- Try asking the SAME question with slightly different wording (e.g.,
  "leaves I can take casually" instead of "casual leave") — semantic search
  should still find the right chunk, even without exact keyword overlap.
- Watch `agent.py`'s output closely: before it prints Saathi's final answer,
  it now prints the **retrieved chunks** — each with a `source`, a
  `chunk_index`, and a `similarity_distance`. None of that comes from the
  LLM. It comes straight from ChromaDB's metadata for the matching chunks.
  This is the actual mechanism behind every citation Saathi gives you.

## 8. Understanding the Vector Store — Metadata, SQLite, and How Citation Really Works

This is the part that usually feels like a black box, so let's open it.

### 8.1 What "metadata" means here

Back in `build_vectorstore.py`, every chunk was stored with a small
dictionary attached to it:
```python
metadatas=[{"source": filename, "chunk_index": i}]
```
That's it — `source` (which policy file this chunk came from) and
`chunk_index` (which piece of that file it is). When `app.py` retrieves the
top-matching chunks for a question, ChromaDB hands back that same metadata
alongside each chunk's text. `app.py` reads `source` straight out of that
metadata to build the `"sources"` list you see in every response — the LLM
itself never "knows" which file it read; **your code** turns metadata into
a citation.

### 8.2 What's actually inside `./chroma_store`

Run this after `build_vectorstore.py`:
```
python inspect_vectorstore.py
```
It does two things:

1. **Through the normal ChromaDB API** — shows your collection's chunk
   count and previews a few chunks with their metadata, exactly as
   `app.py` sees them.
2. **Directly inside `chroma.sqlite3`** — using nothing but Python's
   built-in `sqlite3` module, it lists the real tables ChromaDB created on
   disk and previews a few raw rows from each.

You'll see that the chunk **text and metadata** are stored as perfectly
ordinary rows in a real SQLite database file — no special magic there. The
**vectors themselves** (the embeddings) are handled differently: they're
indexed separately in a structure built for fast nearest-neighbour search
(an HNSW index), stored in per-collection segment files next to the SQLite
file. That's because "which of 31 stored vectors is closest to this new
one" is exactly the kind of question plain SQL rows aren't built to answer
quickly — the same SQL-vs-vector-database distinction covered earlier in
the programme.

### 8.3 How a match gets back to a real policy document

When `app.py` calls `collection.query(...)`, three things happen, in order:

1. ChromaDB searches its vector index for the embeddings closest to your
   question's embedding.
2. It uses the internal ids of those matches to look up the real chunk
   **text and metadata** in the SQLite tables you just previewed.
3. Both are returned together to your Python code — which is why `app.py`
   can build a citation, and why `agent.py` can print exactly which policy,
   which chunk, and how close the match was.

That's the entire path from "a nearest-neighbour number" to "Saathi says
this came from the Leave Policy."

## 9. Troubleshooting

| Problem | Likely cause |
|---|---|
| `ModuleNotFoundError` | Virtual environment not activated, or `pip install -r requirements.txt` not run |
| `AuthenticationError` when running any script | Check `.env` has your real key, correctly quoted, no trailing spaces |
| `app.py` fails with a Chroma "collection not found" error | You haven't run `build_vectorstore.py` yet, or you ran it from a different folder |
| `agent.py` says "Could not reach Saathi" | `app.py` isn't running in the other terminal, or it's on a different port |
| Answers seem to ignore the policies entirely | Check `build_vectorstore.py` actually completed without errors, and that `./chroma_store` exists in this folder |

For SSL/TLS and HTTP 500 troubleshooting on corporate networks, see
`SSL_TLS_ERROR_ANALYSIS.md` in this project root.

## 10. A Note on the Model Name

`CHAT_MODEL` and `EMBED_MODEL` in `app.py` and `build_vectorstore.py` are set
to current models as of this lab's delivery date. Substitute whichever chat
and embedding models your organisation has approved before running this in a
different environment.

## 11. Where This Goes Next

This lab deliberately keeps things simple: one document type (plain `.txt`),
one retrieval step, one LLM call, no memory across questions, no multi-agent
handoff. Modules 4–5 build the fuller version of this pipeline (PDF/Word
ingestion, hybrid search, re-ranking, evaluation); Modules 9–10 turn Saathi
into a stateful, multi-agent system that remembers conversation history and
can hand off between specialised agents. Everything you're running today is
the foundation those modules build on.

# Day 3 — Guided Delivery Solution Files
## Working with LLMs & Agentic AI | NCS Telco+ | NIIT StackRoute
### Module 3: LLM APIs, Structured Outputs & Tool Use

Four self-contained folders, one per practice sheet. Each folder runs independently —
copy any single folder to a fresh machine and it works on its own.

## One-time setup, per folder

```
cd Sheet1_API_Anatomy_Parameters        # or Sheet2 / Sheet3 / Sheet4
python -m venv venv
source venv/bin/activate                 # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then open `.env` in that folder and replace `your-api-key-here` with your real key.
**Never commit `.env` to Git or share it on screen.**

## Running live, during the session

Sheets 1, 2, and 4 are menu-driven runners, same pattern as Day 2:

```
python prompts.py            # lists all 25 prompts with short descriptions
python prompts.py 7          # runs prompt #7 and prints the model's reply
```

Sheet 3 is different — it's a live FastAPI server. See its own section below.

## Folder-by-folder notes

| Folder | Extra setup | What's inside |
|---|---|---|
| `Sheet1_API_Anatomy_Parameters` | none beyond the standard install | Multi-turn `Conversation` class, temperature/max_tokens/stop-sequence experiments |
| `Sheet2_FunctionCalling_MetadataExtractor` | `requirements.txt` also installs `pypdf` | The actual design-doc lab: `extract_document_metadata` tool schema, tested on the two real starter PDFs (already included) |
| `Sheet3_Streaming_FastAPI` | `requirements.txt` also installs `fastapi` + `uvicorn` | `main.py` is a live streaming chatbot backend — see "Running Sheet 3" below |
| `Sheet4_ErrorHandling_Cost_DecisionFramework` | none beyond the standard install | Retry/backoff, token cost tracking, a `BudgetTracker` guardrail, and the prompt/retrieve/fine-tune decision framework |

## Running Sheet 3 (the FastAPI lab)

This one needs two terminals:

**Terminal 1** — start the server and leave it running:
```
cd Sheet3_Streaming_FastAPI
uvicorn main:app --reload --port 8000
```

**Terminal 2** — run prompts against it:
```
curl "http://localhost:8000/chat?q=Explain+EIRP+to+a+field+engineer"
```

`Sheet3_Streaming_FastAPI/README_RUN_ME.md` has the exact curl command for every
FastAPI-specific prompt (#4–6, #10, #13, #15–16, #18–20, #22–23). The rest of that
sheet's prompts (terminal-only streaming demos) run the normal way:
```
python prompts.py 1
```

Also try opening **http://localhost:8000/docs** in a browser while the server runs —
FastAPI's interactive documentation lets you fire requests straight from the page.

## If something fails to run

- `ModuleNotFoundError` → you're not in the activated venv, or forgot `pip install -r requirements.txt`.
- `AuthenticationError` → check `.env` has your real key, with no quotes and no trailing spaces.
- Sheet 2 `FileNotFoundError` on the PDFs → run `prompts.py` from *inside* that folder, not from a parent directory.
- Sheet 3 `curl: (7) Failed to connect` → the `uvicorn` server in Terminal 1 isn't running, or you're using the wrong port.
- Sheet 4 prompts #5 and #13 **deliberately** trigger errors (invalid model / invalid key) to demonstrate retry and error-handling behaviour — that's expected, not a bug.

## A note on the model name

`call_model.py` in every folder sets `MODEL = "gpt-5.4-mini"`. Swap this for whichever
model your organisation has approved by delivery time — the official design doc
references GPT-4o, which was retired from general availability in February 2026.

## A note on Sheet 4's cost figures

`PRICE_PER_MILLION_INPUT` and `PRICE_PER_MILLION_OUTPUT` in Sheet 4's `prompts.py` are
placeholder figures. Replace them with your model's actual published pricing before
using the cost-tracking numbers in front of a client or in a budget conversation.

# Day 2 — Guided Delivery Solution Files
## Working with LLMs & Agentic AI | NCS Telco+ | NIIT StackRoute

Four self-contained folders, one per practice sheet. Each folder runs independently —
copy any single folder to a fresh machine and it works on its own.

## One-time setup, per folder (or once if you reuse a single venv)

```
cd Sheet1_Setup_PromptAnatomy_FewShot        # or Sheet2 / Sheet3 / Sheet4
python -m venv venv
source venv/bin/activate                      # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then open `.env` in that folder and replace `your-api-key-here` with your real key.
**Never commit `.env` to Git or share it on screen.**

## Running live, during the session

Each folder's `prompts.py` is a menu-driven runner:

```
python prompts.py            # lists all 25 prompts with short descriptions
python prompts.py 7          # runs prompt #7 and prints the model's reply
```

Walk through them in order during the session, or jump to whichever number matches
what you're discussing on the corresponding practice sheet.

## Folder-by-folder notes

| Folder | Extra setup | What's inside |
|---|---|---|
| `Sheet1_Setup_PromptAnatomy_FewShot` | none beyond the standard install | `call_model.py` (the reusable base), `prompts.py` (25 zero/one/few-shot prompts) |
| `Sheet2_CoT_StepBack_SystemMessage` | none beyond the standard install | `prompts.py` includes the full Enterprise Assistant `SYSTEM_PROMPT` (the design-doc lab) |
| `Sheet3_StructuredOutput_PromptChains` | `requirements.txt` also installs `pypdf` | `chain.py` (the 2-step extraction+citation chain) reads the two included sample PDFs directly — nothing to configure, just run |
| `Sheet4_Chaining_Injection_Refinement` | none beyond the standard install | `pipeline.py` has the 3-step RFP chain, injection naive-vs-defended pair, and the refinement loop |

## If something fails to run

- `ModuleNotFoundError` → you're not in the activated venv, or forgot `pip install -r requirements.txt`.
- `AuthenticationError` → check `.env` has your real key, with no quotes and no trailing spaces.
- Sheet 3 `FileNotFoundError` on the PDFs → run `prompts.py` from *inside* that folder, not from a parent directory.

## A note on the model name

`call_model.py` in every folder sets `MODEL = "gpt-5.4-mini"`. Swap this for whichever
model your organisation has approved by delivery time — the official design doc
references GPT-4o, which was retired from general availability in February 2026.

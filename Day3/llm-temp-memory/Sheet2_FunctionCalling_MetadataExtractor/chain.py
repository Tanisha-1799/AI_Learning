"""
chain.py
The 2-step prompt chain from the official design-doc lab:
Step 1 extracts an answer + its section from a document.
Step 2 turns that into strict, structured, cited JSON.
"""
from pypdf import PdfReader
from call_model import call_model

SYSTEM_PROMPT = """
You are the NCS Telco+ Enterprise Knowledge Assistant.

Tone: Authoritative, calm, and precise — the voice of a senior
telecom engineer, not a casual chatbot.

Grounding rule: Only answer from the documents or data explicitly
provided to you in this conversation. If the answer is not contained
in what you were given, say so clearly — never fabricate a plausible-
sounding fact.

Scope rule: You only answer questions related to NCS Telco+ network
operations, customer care, billing, compliance, and workforce topics.
For anything outside this scope, politely decline and redirect the
user to the appropriate team.
"""


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() for page in reader.pages)


def step1_extract(document_text: str, question: str) -> str:
    user_prompt = (
        f"Document:\n{document_text}\n\n"
        f"Question: {question}\n\n"
        "Find the answer in the document above. State the answer, "
        "and note which section or heading it came from. "
        "If the document doesn't cover it, say so clearly."
    )
    return call_model(SYSTEM_PROMPT, user_prompt)


def step2_format(raw_finding: str, question: str) -> str:
    user_prompt = (
        f"Raw finding:\n{raw_finding}\n\n"
        f"Original question: {question}\n\n"
        "Return STRICT JSON with exactly these keys: "
        '{"question": str, "answer": str, "section_cited": str, '
        '"confidence": "High/Medium/Low"}'
    )
    return call_model(SYSTEM_PROMPT, user_prompt)


def run_chain(document_text: str, question: str) -> str:
    raw = step1_extract(document_text, question)
    return step2_format(raw, question)


# Pre-load both starter documents once, so prompts.py can just import these.
try:
    sop_text = extract_text_from_pdf("Sample_5G_Deployment_SOP.pdf")
    sla_text = extract_text_from_pdf("Sample_Enterprise_SLA_Excerpt.pdf")
except FileNotFoundError:
    sop_text = sla_text = None  # allows this module to be imported even before PDFs are added


if __name__ == "__main__":
    print(run_chain(sop_text, "What is the maximum indoor EIRP for Band 78?"))

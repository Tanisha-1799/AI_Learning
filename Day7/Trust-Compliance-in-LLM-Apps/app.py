"""
app.py

Pramaan — the NCS Telco+ Trust & Compliance RAG Backend (Step 2 of 3)
==========================================================================
Wires the full trust stack around Disha's basic retrieve-and-answer flow:

    PII-redact question (serving, in)
        -> retrieve
        -> confidence check / refusal
        -> injection scan + untrusted-data wrapping
        -> context assembly
        -> LLM call (citation-required, injection-defended system prompt)
        -> output validation (incl. PII-redact on the way out)
        -> audit log write
        -> return response, with a full per-stage trace

Run AFTER build_vectorstore.py:
    uvicorn app:app --reload --port 8000
"""
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from openai import OpenAI, APIConnectionError, APIStatusError

from context import assemble_context
from pii import redact_pii
from injection_defense import wrap_untrusted, check_retrieved_chunks, INJECTION_DEFENSE_SYSTEM_ADDENDUM
from output_validation import validate_answer, is_refusal, FALLBACK_MESSAGE
from confidence import confidence_level, should_refuse, best_score_from_results
from observability import Tracer
from ssl_network import load_network_settings, create_http_client, print_network_summary
import audit_log

load_dotenv()

CHAT_MODEL = "gpt-5.4-mini"
EMBED_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "pramaan_documents"
PERSIST_DIR = "./chroma_store"
TOP_K = 3

BASE_SYSTEM_PROMPT = """
You are Pramaan, the NCS Telco+ Trust & Compliance Document Q&A Assistant.

Tone: Precise, calm, and technical.

Grounding rule: Only answer using the excerpts provided. Every factual
claim MUST be followed by a citation in the form (Source: <filename>).
If the excerpts don't cover the question, say so plainly and do not guess.
"""

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + INJECTION_DEFENSE_SYSTEM_ADDENDUM

settings = load_network_settings()
print_network_summary(settings)
http_client = create_http_client(settings)

openai_kwargs = {
    "http_client": http_client,
    "max_retries": settings.max_retries,
}
if settings.base_url:
    openai_kwargs["base_url"] = settings.base_url
client = OpenAI(**openai_kwargs)

embed_kwargs = {
    "model": EMBED_MODEL,
    "http_client": http_client,
    "check_embedding_ctx_length": False,
    "request_timeout": settings.timeout_sec,
    "max_retries": settings.max_retries,
}
if settings.base_url:
    embed_kwargs["openai_api_base"] = settings.base_url

embeddings = OpenAIEmbeddings(**embed_kwargs)
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)

app = FastAPI(title="Pramaan - Trust & Compliance RAG Pipeline")


@app.get("/")
def root():
    return {"message": "Pramaan is running. Try /ask?q=your+question"}


@app.get("/ask")
def ask(q: str, top_k: int = TOP_K):
    tracer = Tracer()

    # ---- 1. PII REDACTION, SERVING TIME, ON THE WAY IN ----
    with tracer.stage("pii_redact_input"):
        redacted_question, input_pii_counts = redact_pii(q)
        if input_pii_counts:
            print(f"[Pramaan] PII redacted from incoming question: {input_pii_counts}")

    # ---- 2. RETRIEVAL ----
    with tracer.stage("retrieval"):
        try:
            raw_results = vectorstore.similarity_search_with_relevance_scores(redacted_question, k=top_k)
        except APIConnectionError:
            return {
                "question": redacted_question,
                "answer": "I can't retrieve data right now due to an SSL/OpenAI connection issue.",
                "confidence": "Unavailable",
                "retrieved_chunks": [],
                "sources": [],
                "injection_flagged": False,
                "output_validation_passed": None,
                "trace": tracer.as_dict(),
            }

    best_score = best_score_from_results(raw_results)
    level = confidence_level(best_score)

    # ---- 3. CONFIDENCE CHECK / REFUSAL ----
    if should_refuse(best_score):
        answer = "I don't know — none of the ingested documents cover this question confidently enough for me to answer."
        latency = tracer.total_seconds()
        audit_log.log_request(
            question_redacted=redacted_question,
            retrieved_sources=[doc.metadata.get("source") for doc, _ in raw_results],
            retrieved_scores=[round(s, 4) for _, s in raw_results],
            confidence_level="Refused",
            refused=True,
            injection_flagged=False,
            injection_details="",
            output_validation_passed=None,
            output_validation_details="Skipped — refused before generation.",
            answer=answer,
            cited_sources=[],
            latency_sec=latency,
            prompt_tokens=0,
            completion_tokens=0,
            model=CHAT_MODEL,
        )
        return {
            "question": redacted_question,
            "answer": answer,
            "confidence": "Refused",
            "retrieved_chunks": [],
            "sources": [],
            "injection_flagged": False,
            "output_validation_passed": None,
            "trace": tracer.as_dict(),
        }

    # ---- 4. INJECTION SCAN + UNTRUSTED-DATA WRAPPING ----
    with tracer.stage("injection_scan"):
        chunks_with_sources = [(doc.page_content, doc.metadata.get("source", "unknown")) for doc, _ in raw_results]
        injection_report = check_retrieved_chunks(chunks_with_sources)
        if injection_report["flagged"]:
            print(f"[Pramaan] INJECTION ATTEMPT FLAGGED in retrieved content: {injection_report['details']}")

    # ---- 5. CONTEXT ASSEMBLY (dedupe + pack), then wrap each piece as untrusted data ----
    with tracer.stage("context_assembly"):
        context_text, used_results = assemble_context(raw_results)
        wrapped_pieces = [
            wrap_untrusted(doc.page_content, doc.metadata.get("source", "unknown"))
            for doc, _ in used_results
        ]
        wrapped_context = "\n\n".join(wrapped_pieces)

    retrieved_chunks = [
        {
            "source": doc.metadata.get("source", "unknown"),
            "score": round(float(score), 4),
            "text_preview": doc.page_content[:150] + ("..." if len(doc.page_content) > 150 else ""),
        }
        for doc, score in used_results
    ]

    user_prompt = (
        f"Question: {redacted_question}\n\n"
        f"Retrieved excerpts:\n{wrapped_context}\n\n"
        "Answer using only the excerpts above. Cite each fact as (Source: <filename>)."
    )

    # ---- 6. LLM CALL ----
    with tracer.stage("llm_call"):
        try:
            response = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except APIConnectionError:
            return {
                "question": redacted_question,
                "answer": "I can't generate an answer right now due to an SSL/OpenAI connection issue.",
                "confidence": level,
                "retrieved_chunks": retrieved_chunks,
                "sources": [],
                "injection_flagged": injection_report["flagged"],
                "injection_details": injection_report["details"],
                "output_validation_passed": None,
                "output_validation_details": "Skipped due to API connection error.",
                "trace": tracer.as_dict(),
            }
        except APIStatusError as exc:
            return {
                "question": redacted_question,
                "answer": f"I can't generate an answer right now due to OpenAI API error ({exc.status_code}).",
                "confidence": level,
                "retrieved_chunks": retrieved_chunks,
                "sources": [],
                "injection_flagged": injection_report["flagged"],
                "injection_details": injection_report["details"],
                "output_validation_passed": None,
                "output_validation_details": "Skipped due to API status error.",
                "trace": tracer.as_dict(),
            }
    raw_answer = response.choices[0].message.content
    usage = response.usage

    # ---- 7. OUTPUT VALIDATION (includes re-scanning the OUTPUT for PII) ----
    with tracer.stage("output_validation"):
        validation = validate_answer(raw_answer)
        if validation["passed"]:
            final_answer = raw_answer
        else:
            print(f"[Pramaan] OUTPUT VALIDATION FAILED: {validation['details']}")
            final_answer = FALLBACK_MESSAGE

    cited_sources = sorted(set(doc.metadata.get("source", "unknown") for doc, _ in used_results)) \
        if not is_refusal(final_answer) else []

    # ---- 8. AUDIT LOG ----
    latency = tracer.total_seconds()
    audit_log.log_request(
        question_redacted=redacted_question,
        retrieved_sources=[c["source"] for c in retrieved_chunks],
        retrieved_scores=[c["score"] for c in retrieved_chunks],
        confidence_level=level,
        refused=False,
        injection_flagged=injection_report["flagged"],
        injection_details=str(injection_report["details"]),
        output_validation_passed=validation["passed"],
        output_validation_details=validation["details"],
        answer=final_answer,
        cited_sources=cited_sources,
        latency_sec=latency,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        model=CHAT_MODEL,
    )

    return {
        "question": redacted_question,
        "answer": final_answer,
        "confidence": level,
        "retrieved_chunks": retrieved_chunks,
        "sources": cited_sources,
        "injection_flagged": injection_report["flagged"],
        "injection_details": injection_report["details"],
        "output_validation_passed": validation["passed"],
        "output_validation_details": validation["details"],
        "trace": tracer.as_dict(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

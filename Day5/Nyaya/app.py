"""
app.py

Nyaya - Legal and Compliance Document Q&A Pipeline (Step 2 of 3)
=================================================================
Implements the rest of the RAG architecture: retrieve -> assemble context
(dedupe + pack) -> answer -> cite (or say "I don't know").

Run AFTER build_vectorstore.py has been run at least once:
    uvicorn app:app --reload --port 8000

Try a question directly in a browser once running:
    http://localhost:8000/ask?q=What+is+the+maximum+indoor+EIRP+for+Band+78%3F
"""
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from openai import OpenAI, APIConnectionError, APIStatusError

from retrieval import retrieve
from context import assemble_context

load_dotenv()


def create_http_client() -> httpx.Client:
    """Create an HTTP client with optional TLS overrides from environment."""
    ca_bundle = os.getenv("OPENAI_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    allow_insecure_ssl = os.getenv("ALLOW_INSECURE_SSL", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }

    if ca_bundle:
        # Keep requests/tiktoken trust chain aligned with the same custom CA.
        os.environ["SSL_CERT_FILE"] = ca_bundle
        os.environ["REQUESTS_CA_BUNDLE"] = ca_bundle
        os.environ["CURL_CA_BUNDLE"] = ca_bundle

    if allow_insecure_ssl:
        print("WARNING: SSL certificate verification is disabled (ALLOW_INSECURE_SSL=true).")
        print("         Use this only for local debugging and never in production.\n")

    verify_setting = ca_bundle if ca_bundle else (False if allow_insecure_ssl else True)
    return httpx.Client(verify=verify_setting, timeout=60.0)

CHAT_MODEL = "gpt-5.4-mini"             # substitute your organisation's approved model
EMBED_MODEL = "text-embedding-3-small"   # must match build_vectorstore.py
COLLECTION_NAME = "nyaya_documents"
PERSIST_DIR = "./chroma_store"
MIN_CONFIDENCE = 0.3   # below this relevance score, we refuse to answer rather than guess

SYSTEM_PROMPT = """
You are Nyaya, the NCS Telco+ Legal and Compliance Document Q&A Assistant.

Tone: Precise, calm, and professional.

Grounding rule: Only answer using the excerpts provided in each question.
Every factual claim in your answer MUST be followed by a citation in the
form (Source: <filename>). If the excerpts don't cover the question, say
so plainly and do not guess.
"""

http_client = create_http_client()
client = OpenAI(http_client=http_client)
embeddings = OpenAIEmbeddings(
    model=EMBED_MODEL,
    http_client=http_client,
    # Avoid local tokenizer downloads (tiktoken/HuggingFace) in restricted TLS networks.
    # Query text sizes here are small enough for embedding limits.
    check_embedding_ctx_length=False,
)
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)

app = FastAPI(title="Nyaya - NCS Telco+ Legal and Compliance Document Q&A Pipeline")


@app.get("/")
def root():
    return {"message": "Nyaya is running. Try /ask?q=your+question&pattern=topk"}


@app.get("/ask")
def ask(q: str, pattern: str = "topk", k: int = 3):
    """
    pattern: "topk" (default), "mmr", or "threshold" — see retrieval.py
    k: how many chunks to retrieve
    """
    try:
        results = retrieve(vectorstore, q, pattern=pattern, k=k)
    except APIConnectionError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "OpenAI connection/TLS error while embedding the question. "
                "If you are on a corporate network, set OPENAI_CA_BUNDLE to your "
                "trusted CA file, or ALLOW_INSECURE_SSL=true for local-only testing."
            ),
        ) from exc
    except APIStatusError as exc:
        raise HTTPException(status_code=exc.status_code, detail=f"OpenAI API error: {exc}") from exc

    # "I don't know" guardrail. If nothing came back, or the best available
    # score is below our confidence floor, refuse to answer rather than
    # asking the LLM to generate something from weak or no evidence.
    scored = [(doc, score) for doc, score in results if score is not None]
    best_score = max((score for _, score in scored), default=None)
    if not results or (best_score is not None and best_score < MIN_CONFIDENCE):
        return {
            "question": q,
            "pattern": pattern,
            "retrieved_chunks": [],
            "answer": ("I don't know \u2014 none of the ingested documents cover this "
                       "question confidently enough for me to answer."),
            "sources": [],
        }

    context_text, used_results = assemble_context(results)

    retrieved_chunks = [
        {
            "source": doc.metadata.get("source", "unknown"),
            "metadata": {k2: v for k2, v in doc.metadata.items() if k2 != "source"},
            "relevance_score": round(score, 4) if score is not None else None,
            "text_preview": doc.page_content[:150] + ("..." if len(doc.page_content) > 150 else ""),
        }
        for doc, score in used_results
    ]

    user_prompt = (
        f"Question: {q}\n\n"
        f"Retrieved excerpts:\n{context_text}\n\n"
        "Answer using only the excerpts above. Cite each fact as (Source: <filename>)."
    )

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    except APIConnectionError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "OpenAI connection/TLS error while generating the answer. "
                "Check CA/proxy settings or use ALLOW_INSECURE_SSL=true for local testing."
            ),
        ) from exc
    except APIStatusError as exc:
        raise HTTPException(status_code=exc.status_code, detail=f"OpenAI API error: {exc}") from exc

    return {
        "question": q,
        "pattern": pattern,
        "retrieved_chunks": retrieved_chunks,
        "answer": response.choices[0].message.content,
        "sources": sorted(set(doc.metadata.get("source", "unknown") for doc, _ in used_results)),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

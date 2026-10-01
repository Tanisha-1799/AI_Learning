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

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from openai import OpenAI, APIConnectionError, APIStatusError

from retrieval import retrieve
from context import assemble_context
from ssl_network import load_network_settings, create_http_client, print_network_summary

load_dotenv()

CHAT_MODEL = "gpt-5.4-mini"             # substitute your organisation's approved model
EMBED_MODEL = "text-embedding-3-small"   # must match build_vectorstore.py
COLLECTION_NAME = "nyaya_documents"
PERSIST_DIR = "./chroma_store"
MIN_CONFIDENCE = float(os.getenv("NYAYA_MIN_CONFIDENCE", "0.2"))

SYSTEM_PROMPT = """
You are Nyaya, the NCS Telco+ Legal and Compliance Document Q&A Assistant.

Tone: Precise, calm, and professional.

Grounding rule: Only answer using the excerpts provided in each question.
Every factual claim in your answer MUST be followed by a citation in the
form (Source: <filename>). If the excerpts don't cover the question, say
so plainly and do not guess.
"""

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
    # Avoid local tokenizer downloads (tiktoken/HuggingFace) in restricted TLS networks.
    # Query text sizes here are small enough for embedding limits.
    "check_embedding_ctx_length": False,
    "request_timeout": settings.timeout_sec,
    "max_retries": settings.max_retries,
}
if settings.base_url:
    embed_kwargs["openai_api_base"] = settings.base_url

embeddings = OpenAIEmbeddings(
    **embed_kwargs,
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

    # "I don't know" guardrail:
    # - For topk/mmr, return available context and let grounded prompting decide.
    # - For threshold, enforce an explicit confidence floor.
    scored = [(doc, score) for doc, score in results if score is not None]
    best_score = max((score for _, score in scored), default=None)
    enforce_confidence = pattern == "threshold"
    if not results or (enforce_confidence and best_score is not None and best_score < MIN_CONFIDENCE):
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

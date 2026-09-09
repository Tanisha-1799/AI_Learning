"""
app.py

Kosh - the NCS Telco+ Finance Knowledge Assistant
=================================================
Step 2 of 3: RAG backend API.

Run after building the vector store:
    uvicorn app:app --reload --port 8000
"""
import os

import chromadb
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError, OpenAI

load_dotenv()


CHAT_MODEL = "gpt-5.4-mini"
EMBED_MODEL = "text-embedding-3-small"
TOP_K = 3
COLLECTION_NAME = "finance_docs"

SYSTEM_PROMPT = """
You are Kosh, the NCS Telco+ Finance Knowledge Assistant.

Tone: Precise, clear, and numbers-first. Keep answers concise and easy to audit.

Grounding rule: Only answer using the Finance policy excerpts provided in this
request. If excerpts do not contain the exact number, threshold, timeline, or
approval authority, say you do not have enough policy context and ask the user
to confirm with Finance Ops. Never guess monetary values or terms.

Scope rule: Do not provide tax advice, legal advice, payroll calculations, or
personal financial planning. Stay within internal Finance policy interpretation.

Always mention which policy document(s) your answer is based on.
"""


def create_openai_client():
    """Create OpenAI client with optional TLS overrides from environment."""
    ca_bundle = os.getenv("OPENAI_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    allow_insecure_ssl = os.getenv("ALLOW_INSECURE_SSL", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }

    if allow_insecure_ssl:
        print("WARNING: SSL certificate verification is disabled (ALLOW_INSECURE_SSL=true).")
        print("         Use this only for local debugging and never in production.\n")

    verify_setting = ca_bundle if ca_bundle else (False if allow_insecure_ssl else True)
    http_client = httpx.Client(verify=verify_setting, timeout=60.0)
    return OpenAI(http_client=http_client)


client = create_openai_client()
chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_collection(COLLECTION_NAME)

app = FastAPI(title="Kosh - NCS Telco+ Finance Knowledge Assistant")


def embed_query(text: str):
    response = client.embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding


def retrieve_context(question: str, top_k: int = TOP_K):
    query_embedding = embed_query(question)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    sources = [meta["source"] for meta in metadatas]
    chunk_indices = [meta["chunk_index"] for meta in metadatas]
    return chunks, sources, chunk_indices, distances


@app.get("/")
def root():
    return {"message": "Kosh is running. Try /ask?q=your+question+here"}


@app.get("/ask")
def ask(q: str):
    try:
        chunks, sources, chunk_indices, distances = retrieve_context(q)
    except APIConnectionError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "OpenAI connection/TLS error while embedding your question. "
                "Set OPENAI_CA_BUNDLE to a trusted CA file or use "
                "ALLOW_INSECURE_SSL=true for local-only testing."
            ),
        ) from exc
    except APIStatusError as exc:
        raise HTTPException(status_code=exc.status_code, detail=f"OpenAI API error: {exc}") from exc

    context_text = "\n\n---\n\n".join(
        f"(From {source}, chunk #{chunk_index})\n{chunk}"
        for chunk, source, chunk_index in zip(chunks, sources, chunk_indices)
    )

    user_prompt = (
        f"Employee question: {q}\n\n"
        f"Relevant Finance policy excerpts:\n{context_text}\n\n"
        "Answer using only the excerpts above. If exact numbers are missing, say so clearly."
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

    retrieved_chunks = [
        {
            "source": source,
            "chunk_index": chunk_index,
            "similarity_distance": round(distance, 4),
            "text_preview": chunk[:150] + ("..." if len(chunk) > 150 else ""),
        }
        for chunk, source, chunk_index, distance in zip(chunks, sources, chunk_indices, distances)
    ]

    return {
        "question": q,
        "retrieved_chunks": retrieved_chunks,
        "answer": response.choices[0].message.content,
        "sources": sorted(set(sources)),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
app.py

Saathi — the NCS Telco+ HR Policy Assistant
============================================
Step 2 of 3: the RAG backend.

This is a small FastAPI server. When it receives a question, it:
  1. Turns the question into a vector (embeds it)
  2. Searches the ChromaDB vector store for the most relevant policy chunks
  3. Hands those chunks + the question to the LLM
  4. Returns a grounded answer, citing which policy document(s) it used

Run this AFTER build_vectorstore.py has been run at least once:
    uvicorn app:app --reload --port 8000

Leave this running in its own terminal — agent.py (in a second terminal)
will talk to it.
"""
import chromadb
import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APIStatusError
from fastapi import FastAPI, HTTPException

load_dotenv()


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

CHAT_MODEL = "gpt-5.4-mini"          # substitute your organisation's approved model
EMBED_MODEL = "text-embedding-3-small"
TOP_K = 3                             # how many policy chunks to retrieve per question

SYSTEM_PROMPT = """
You are Saathi, the NCS Telco+ HR Policy Assistant.

Tone: Warm, clear, and helpful — like a knowledgeable HR colleague, not a
robotic FAQ bot.

Grounding rule: Only answer using the policy excerpts you are given in each
question. If the excerpts don't fully cover what's being asked, say so
honestly and suggest the employee contact the relevant HR/Finance team
directly — never invent a policy detail that isn't in the excerpts.

Always mention which policy document(s) your answer is based on, by name.
"""

# Connect to the vector store built by build_vectorstore.py.
# If this fails, you forgot to run build_vectorstore.py first.
chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_collection("hr_policies")

app = FastAPI(title="Saathi - NCS Telco+ HR Policy Assistant")


def embed_query(text: str):
    response = client.embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding


def retrieve_context(question: str, top_k: int = TOP_K):
    """Embed the question, then find the most similar policy chunks.

    Returns four parallel lists: the chunk text, which policy file each
    chunk came from, that chunk's index within its file, and how close
    (in vector space) each chunk was to the question — all of this comes
    straight from ChromaDB's metadata, which is what makes citation
    possible in the first place.
    """
    query_embedding = embed_query(question)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    sources = [m["source"] for m in metadatas]
    chunk_indices = [m["chunk_index"] for m in metadatas]
    return chunks, sources, chunk_indices, distances


@app.get("/")
def root():
    return {"message": "Saathi is running. Try /ask?q=your+question+here"}


@app.get("/ask")
def ask(q: str):
    """The main endpoint. Example: /ask?q=How many casual leaves do I get?"""
    try:
        chunks, sources, chunk_indices, distances = retrieve_context(q)
    except APIConnectionError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "OpenAI connection/TLS error while embedding your question. "
                "If you are on a corporate network, set OPENAI_CA_BUNDLE to your "
                "trusted CA file, or ALLOW_INSECURE_SSL=true for local-only testing."
            ),
        ) from exc
    except APIStatusError as exc:
        raise HTTPException(status_code=exc.status_code, detail=f"OpenAI API error: {exc}") from exc

    context_text = "\n\n---\n\n".join(
        f"(From {src}, chunk #{idx})\n{chunk}"
        for chunk, src, idx in zip(chunks, sources, chunk_indices)
    )

    user_prompt = (
        f"Employee question: {q}\n\n"
        f"Relevant policy excerpts:\n{context_text}\n\n"
        "Answer the employee's question using only the excerpts above."
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

    # This is the part worth pausing on: everything in "retrieved_chunks"
    # comes directly from ChromaDB's metadata for each chunk — the source
    # filename and chunk_index we attached back in build_vectorstore.py,
    # plus the distance score ChromaDB computed during the similarity
    # search. The LLM never "knows" which file it read; your code is what
    # turns that metadata back into a citation.
    retrieved_chunks = [
        {
            "source": src,
            "chunk_index": idx,
            "similarity_distance": round(dist, 4),
            "text_preview": chunk[:150] + ("..." if len(chunk) > 150 else ""),
        }
        for chunk, src, idx, dist in zip(chunks, sources, chunk_indices, distances)
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

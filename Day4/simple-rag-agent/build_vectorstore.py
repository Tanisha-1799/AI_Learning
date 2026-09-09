"""
build_vectorstore.py

Saathi — the NCS Telco+ HR Policy Assistant
============================================
Step 1 of 3: build the knowledge base.

This script reads every HR policy in the policies/ folder, splits each one
into small chunks, converts each chunk into a vector (an embedding) using
OpenAI's embedding model, and stores everything in a ChromaDB vector store
saved to disk in ./chroma_store.

Run this ONCE (and again any time you add or edit a policy file):
    python build_vectorstore.py

You should see it print progress for each of the 5 policy documents, then
a final confirmation message. After that, you're ready to start app.py.
"""
import os
import glob
import sys
import chromadb
import httpx
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError

load_dotenv()


def create_openai_client():
    """Create an OpenAI client with optional TLS overrides from environment."""
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

EMBED_MODEL = "text-embedding-3-small"

# Kept deliberately simple and explainable: fixed-size chunks with a small
# overlap, rather than a smarter sentence-aware or heading-aware splitter.
CHUNK_SIZE = 500     # characters per chunk
CHUNK_OVERLAP = 50   # characters shared between consecutive chunks, so an
                      # idea that falls on a chunk boundary isn't lost


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping fixed-size chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def embed(text):
    """Turn one piece of text into a vector using OpenAI's embedding model."""
    response = client.embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding


def main():
    print("=" * 60)
    print("Saathi — Building the HR Policy Vector Store")
    print("=" * 60)

    chroma_client = chromadb.PersistentClient(path="./chroma_store")

    # Start fresh every time this script runs, so re-running it after
    # editing a policy doesn't leave old, duplicate, or stale chunks behind.
    try:
        chroma_client.delete_collection("hr_policies")
    except Exception:
        pass
    collection = chroma_client.create_collection("hr_policies")

    policy_files = sorted(glob.glob("policies/*.txt"))
    if not policy_files:
        print("No policy files found in policies/ — nothing to build.")
        return

    print(f"\nFound {len(policy_files)} policy document(s):")
    for f in policy_files:
        print(f"  - {os.path.basename(f)}")
    print()

    total_chunks = 0
    for filepath in policy_files:
        filename = os.path.basename(filepath)
        print(f"Processing {filename} ...")

        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            try:
                embedding = embed(chunk)
            except APIConnectionError as exc:
                print("\nEmbedding request failed due to a connection/TLS issue.")
                print("If your company uses SSL inspection, configure a trusted CA bundle:")
                print("  PowerShell example:")
                print("    $env:OPENAI_CA_BUNDLE = 'C:\\path\\corp-root-ca.pem'")
                print("For local-only testing (unsafe), you can bypass verification:")
                print("    $env:ALLOW_INSECURE_SSL = 'true'")
                print(f"\nOriginal error: {exc}")
                sys.exit(1)
            collection.add(
                ids=[f"{filename}-{i}"],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": filename, "chunk_index": i}],
            )
        print(f"  -> {len(chunks)} chunks embedded and stored.\n")
        total_chunks += len(chunks)

    print("=" * 60)
    print(f"Done. {total_chunks} total chunks stored in ./chroma_store")
    print("Next step: start app.py (see README.md)")
    print("=" * 60)


if __name__ == "__main__":
    main()

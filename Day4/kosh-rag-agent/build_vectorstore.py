"""
build_vectorstore.py

Kosh - the NCS Telco+ Finance Knowledge Assistant
=================================================
Step 1 of 3: build the finance knowledge base.

This script reads every Finance policy in the policies/ folder, splits each one
into chunks, converts each chunk into an embedding, and stores everything in a
ChromaDB vector store in ./chroma_store.

Run this ONCE (and again after editing policy files):
    python build_vectorstore.py
"""
import glob
import os
import sys

import chromadb
import httpx
from dotenv import load_dotenv
from openai import APIConnectionError, OpenAI

load_dotenv()


EMBED_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
COLLECTION_NAME = "finance_docs"


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
    """Embed one text chunk."""
    response = client.embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding


def main():
    print("=" * 60)
    print("Kosh - Building the Finance Policy Vector Store")
    print("=" * 60)

    chroma_client = chromadb.PersistentClient(path="./chroma_store")

    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = chroma_client.create_collection(COLLECTION_NAME)

    policy_files = sorted(glob.glob("policies/*.txt"))
    if not policy_files:
        print("No policy files found in policies/ - nothing to build.")
        return

    print(f"\nFound {len(policy_files)} policy document(s):")
    for file_path in policy_files:
        print(f"  - {os.path.basename(file_path)}")
    print()

    total_chunks = 0
    for file_path in policy_files:
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name} ...")

        with open(file_path, "r", encoding="utf-8") as file_obj:
            text = file_obj.read()

        chunks = chunk_text(text)
        for index, chunk in enumerate(chunks):
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
                ids=[f"{file_name}-{index}"],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": file_name, "chunk_index": index}],
            )

        print(f"  -> {len(chunks)} chunks embedded and stored.\n")
        total_chunks += len(chunks)

    print("=" * 60)
    print(f"Done. {total_chunks} total chunks stored in ./chroma_store")
    print("Next step: start app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()

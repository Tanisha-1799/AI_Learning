"""
build_vectorstore.py

Pramaan — Build the Knowledge Base (Step 1 of 3)
=====================================================
Same ingest -> chunk -> embed -> index flow as Disha (Day 5). PII
redaction at ingest time happens here, same as before — Pramaan's NEW
PII handling (at serving time, on both the question and the answer)
lives in app.py, not here.

Run:
    python build_vectorstore.py
"""
import glob
import os
import shutil
import sys

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from openai import OpenAI, APIConnectionError, APIStatusError

from loaders import load_document
from chunking import chunk_text
from pii import redact_pii
from ssl_network import (
    load_network_settings,
    create_http_client,
    print_network_summary,
    print_connection_guidance,
    describe_exception,
)

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "pramaan_documents"
PERSIST_DIR = "./chroma_store"


def build():
    print("=" * 64)
    print("Pramaan — Building the Knowledge Base")
    print("=" * 64)

    filepaths = sorted(glob.glob("documents/*"))
    if not filepaths:
        print("No documents found in documents/ — nothing to build.")
        return

    print(f"\nFound {len(filepaths)} source document(s):")
    for f in filepaths:
        print(f"  - {os.path.basename(f)}")

    all_documents = []
    total_pii_redactions = {}

    for filepath in filepaths:
        filename = os.path.basename(filepath)
        print(f"\nProcessing {filename} ...")

        raw_units = load_document(filepath)
        print(f"  Loaded as {len(raw_units)} source unit(s)")

        file_chunk_count = 0
        for unit in raw_units:
            redacted_text, pii_counts = redact_pii(unit["text"])
            for label, count in pii_counts.items():
                total_pii_redactions[label] = total_pii_redactions.get(label, 0) + count

            chunks = chunk_text(redacted_text)
            for i, chunk in enumerate(chunks):
                metadata = dict(unit["metadata"])
                metadata["chunk_index"] = i
                all_documents.append(Document(page_content=chunk, metadata=metadata))
                file_chunk_count += 1

        print(f"  -> {file_chunk_count} chunk(s) from this file")

    print(f"\nTotal chunks to embed: {len(all_documents)}")
    if total_pii_redactions:
        print(f"PII redacted at INGEST time: {total_pii_redactions}")
    else:
        print("No PII patterns matched during ingestion.")

    print("\nEmbedding and storing in ChromaDB...")
    settings = load_network_settings()
    print_network_summary(settings)
    http_client = create_http_client(settings)

    openai_kwargs = {
        "http_client": http_client,
        "max_retries": settings.max_retries,
    }
    if settings.base_url:
        openai_kwargs["base_url"] = settings.base_url

    # Connectivity preflight so failures are reported before chunk upload begins.
    try:
        OpenAI(**openai_kwargs).models.list()
    except APIStatusError as exc:
        print(f"OpenAI preflight returned API status {exc.status_code}; proceeding to embedding call.")
    except APIConnectionError as exc:
        print("\nOpenAI preflight failed before embedding upload.")
        print_connection_guidance()
        print(f"\nOriginal error: {describe_exception(exc)}")
        sys.exit(1)

    embed_kwargs = {
        "model": EMBED_MODEL,
        "http_client": http_client,
        "check_embedding_ctx_length": False,
        "request_timeout": settings.timeout_sec,
        "max_retries": settings.max_retries,
    }
    if settings.base_url:
        embed_kwargs["openai_api_base"] = settings.base_url

    embeddings = OpenAIEmbeddings(
        **embed_kwargs,
    )

    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)

    try:
        Chroma.from_documents(
            documents=all_documents,
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            persist_directory=PERSIST_DIR,
        )
    except APIConnectionError as exc:
        print("\nEmbedding request failed due to a connection/TLS issue.")
        print_connection_guidance()
        print(f"\nOriginal error: {describe_exception(exc)}")
        sys.exit(1)

    print("\n" + "=" * 64)
    print(f"Done. {len(all_documents)} chunks stored in {PERSIST_DIR}")
    print("Next step: start app.py (see README.md)")
    print("=" * 64)


if __name__ == "__main__":
    build()

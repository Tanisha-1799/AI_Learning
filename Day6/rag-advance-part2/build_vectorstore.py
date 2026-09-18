"""
build_vectorstore.py

Samiksha — Build the Knowledge Base (Step 1 of 3)
=====================================================
Same ingest -> chunk -> embed -> index flow as Day 5's Disha lab, with
metadata enrichment added: every chunk is now stamped with doc_type,
version, and effective_date, in addition to source and chunk_index.

Run:
    python build_vectorstore.py
"""
import glob
import os
import shutil
import sys
import stat
import time

import httpx
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from openai import APIConnectionError

from loaders import load_document
from chunking import chunk_text
from pii import redact_pii
from metadata_enrichment import enrich_document

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "samiksha_documents"
PERSIST_DIR = "./chroma_store"


def create_http_client() -> httpx.Client:
    """Create an HTTP client with optional TLS overrides from environment."""
    ca_bundle = os.getenv("OPENAI_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    allow_insecure_ssl = os.getenv("ALLOW_INSECURE_SSL", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }

    if ca_bundle and not os.path.isfile(ca_bundle):
        print(f"WARNING: CA bundle path does not exist: {ca_bundle}")
        print("         Falling back to default TLS trust store for this run.")
        ca_bundle = None

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


def build():
    print("=" * 64)
    print("Samiksha — Building the Knowledge Base (with metadata enrichment)")
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

        # Enrich once per file. For pdf/docx/html we pass the first unit's
        # text as a sample to search for the "Version: X | Effective
        # Date: Y" header line; json/csv read the file directly instead.
        sample_text = raw_units[0]["text"] if raw_units else ""
        doc_metadata = enrich_document(filepath, sample_text=sample_text)
        print(f"  Enriched metadata: {doc_metadata}")

        file_chunk_count = 0
        for unit in raw_units:
            redacted_text, pii_counts = redact_pii(unit["text"])
            for label, count in pii_counts.items():
                total_pii_redactions[label] = total_pii_redactions.get(label, 0) + count

            chunks = chunk_text(redacted_text)
            for i, chunk in enumerate(chunks):
                # Start from this unit's own metadata (e.g. page number,
                # or row_id for CSV), then layer the document-level
                # enrichment on top, then set the chunk's own index.
                metadata = dict(unit["metadata"])
                metadata.update(doc_metadata)
                metadata["chunk_index"] = i
                all_documents.append(Document(page_content=chunk, metadata=metadata))
                file_chunk_count += 1

        print(f"  -> {file_chunk_count} chunk(s) from this file")

    print(f"\nTotal chunks to embed: {len(all_documents)}")
    if total_pii_redactions:
        print(f"PII redacted during ingestion: {total_pii_redactions}")
    else:
        print("No PII patterns matched during ingestion.")

    print("\nEmbedding and storing in ChromaDB (this calls the OpenAI API)...")
    http_client = create_http_client()
    embeddings = OpenAIEmbeddings(
        model=EMBED_MODEL,
        http_client=http_client,
        # Avoid local tokenizer downloads (tiktoken/HuggingFace) in restricted TLS networks.
        check_embedding_ctx_length=False,
    )

    if os.path.exists(PERSIST_DIR):
        def _on_rm_error(func, path, exc_info):
            # OneDrive/Windows can mark files read-only; make writable and retry.
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass

        removed = False
        last_error = None
        for _ in range(3):
            try:
                shutil.rmtree(PERSIST_DIR, onerror=_on_rm_error)
                removed = True
                break
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.8)

        if not removed:
            print("\nCould not clear ./chroma_store due to a file lock.")
            print("This usually means app.py/uvicorn is still running and holding chroma.sqlite3.")
            print("Stop the API process first, then rerun build_vectorstore.py.")
            print(f"Original error: {last_error}")
            sys.exit(1)

    try:
        Chroma.from_documents(
            documents=all_documents,
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            persist_directory=PERSIST_DIR,
        )
    except APIConnectionError as exc:
        print("\nEmbedding request failed due to a connection/TLS issue.")
        print("If your company uses SSL inspection, configure a trusted CA bundle:")
        print("  PowerShell example:")
        print("    $env:OPENAI_CA_BUNDLE = 'C:\\path\\corp-root-ca.pem'")
        print("For local-only testing (unsafe), you can bypass verification:")
        print("    $env:ALLOW_INSECURE_SSL = 'true'")
        print(f"\nOriginal error: {exc}")
        sys.exit(1)

    print("\n" + "=" * 64)
    print(f"Done. {len(all_documents)} chunks stored in {PERSIST_DIR}")
    print("Next step: start app.py (see README.md)")
    print("=" * 64)


if __name__ == "__main__":
    build()

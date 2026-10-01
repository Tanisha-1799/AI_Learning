"""
starter/build_vectorstore.py — Solstice Insurance (Claims Support)

============================ YOUR TASK ============================
This is a TAKE-HOME assignment. Fill in every TODO based on the
predictions you wrote in Part 1 of the worksheet, using your OWN
reasoning about Solstice's specific requirements — not by copying
Meridian's answers. The two scenarios have genuinely different
technical demands; a matching answer to Meridian's would likely be
WRONG here.
======================================================================
"""

import glob
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "toolkit"))

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# TODO 1: Import the correct loader functions from toolkit/loaders.py.
from loaders import load_pdf, load_html, load_csv, load_json

from chunking import chunk_text
from pii import redact_pii

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "solstice_documents"
PERSIST_DIR = "./chroma_store"

# TODO 2:
# The Claims Processing SOP has clearly separated numbered sections,
# so heading-aware chunking is appropriate.
CHUNK_STRATEGY = "heading_aware"


def extract_document_metadata(text: str) -> dict:
    """
    Extract document-level metadata from the source text.
    """

    metadata = {}

    document_id = re.search(
        r"Document ID:\s*([A-Za-z0-9_-]+)",
        text,
        re.IGNORECASE
    )

    version = re.search(
        r"Version:\s*([0-9.]+)",
        text,
        re.IGNORECASE
    )

    effective_date = re.search(
        r"Effective Date:\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2})",
        text,
        re.IGNORECASE
    )

    if document_id:
        metadata["document_id"] = document_id.group(1)

    if version:
        metadata["version"] = version.group(1)

    if effective_date:
        metadata["effective_date"] = effective_date.group(1)

    return metadata


def build():
    print("=" * 64)
    print("Solstice Insurance — Building the Knowledge Base")
    print(f"Chunking strategy in use: {CHUNK_STRATEGY}")
    print("=" * 64)

    filepaths = sorted(glob.glob("../documents/*"))
    all_documents = []
    total_pii_redactions = {}

    for filepath in filepaths:
        filename = os.path.basename(filepath)
        print(f"\nProcessing {filename} ...")

        # ----------------------------------------------------------
        # TODO 4: Load, redact PII, chunk, and build Document objects
        # ----------------------------------------------------------

        extension = os.path.splitext(filename)[1].lower()

        if extension == ".pdf":
            units = load_pdf(filepath)

        elif extension == ".html":
            units = load_html(filepath)

        elif extension == ".csv":
            # Solstice uses claim_id as the row identifier.
            units = load_csv(filepath, id_column="claim_id")

        elif extension == ".json":
            # Solstice JSON uses coverage_tiers as its top-level list.
            units = load_json(filepath, list_key="coverage_tiers")

        else:
            print(f"Skipping unsupported file type: {filename}")
            continue

        # ----------------------------------------------------------
        # Extract document-level metadata.
        #
        # For PDF/HTML, metadata is in the source text.
        # For JSON, metadata is stored outside coverage_tiers,
        # so it is not included by load_json().
        # ----------------------------------------------------------

        combined_text = "\n".join(
            unit["text"]
            for unit in units
        )

        document_metadata = extract_document_metadata(combined_text)

        # ----------------------------------------------------------
        # JSON metadata is outside the coverage_tiers list.
        # Add it explicitly for the Solstice coverage document.
        # ----------------------------------------------------------

        if extension == ".json":
            document_metadata = {
                "document_id": "SOL-UW-TIERS-02",
                "version": "2.0",
                "effective_date": "2026-01-15",
            }

        # ----------------------------------------------------------
        # Process each loader unit
        # ----------------------------------------------------------

        for unit_index, unit in enumerate(units):

            text = unit["text"]

            if not text.strip():
                continue

            # ------------------------------------------------------
            # TODO 3:
            #
            # customer_note is unreviewed free text.
            # We keep it as source data, but redact PII before
            # embedding. Prompt-injection defence is handled later
            # during retrieval/application processing.
            # ------------------------------------------------------

            redacted_text, redaction_counts = redact_pii(text)

            for pii_type, count in redaction_counts.items():
                total_pii_redactions[pii_type] = (
                    total_pii_redactions.get(pii_type, 0) + count
                )

            # ------------------------------------------------------
            # Chunking
            #
            # CSV:
            #   one claim row = one chunk.
            #
            # JSON:
            #   one coverage tier = one chunk.
            #
            # PDF:
            #   use heading-aware chunking.
            #
            # HTML:
            #   loader already separates each FAQ section, so
            #   preserve those logical units.
            # ------------------------------------------------------

            if extension in [".csv", ".json", ".html"]:
                chunks = [redacted_text]
            else:
                chunks = chunk_text(
                    redacted_text,
                    strategy=CHUNK_STRATEGY
                )

            # ------------------------------------------------------
            # Build LangChain Documents
            # ------------------------------------------------------

            for chunk_index, chunk in enumerate(chunks):

                if not chunk.strip():
                    continue

                metadata = {
                    "source": filename,
                    "chunk_index": chunk_index,
                    "unit_index": unit_index,
                }

                # Preserve metadata produced by the shared loader.
                metadata.update(unit.get("metadata", {}))

                # Add document-level metadata.
                metadata.update(document_metadata)

                all_documents.append(
                    Document(
                        page_content=chunk,
                        metadata=metadata
                    )
                )

    print(f"\nTotal chunks to embed: {len(all_documents)}")

    if total_pii_redactions:
        print(f"PII redacted at ingest: {total_pii_redactions}")
    else:
        print("PII redacted at ingest: none")

    # TODO 5: Embed and store in ChromaDB.

    embeddings = OpenAIEmbeddings(
        model=EMBED_MODEL
    )

    Chroma.from_documents(
        documents=all_documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR,
    )

    print("Build complete. Next: fill in ../starter/app.py")


if __name__ == "__main__":
    build()
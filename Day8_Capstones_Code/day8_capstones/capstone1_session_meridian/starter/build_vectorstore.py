"""
starter/build_vectorstore.py — Meridian Freight & Logistics

============================ YOUR TASK ============================
Fill in the TODOs below based on the predictions you wrote in Part 1
of the worksheet. Don't just make it run — make your choices match
your reasoning about THIS client's specific needs.
======================================================================

Read documents/, redact PII, chunk, embed, and store in ChromaDB.
"""

import glob
import os
import re
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "toolkit")
)

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from loaders import load_pdf, load_html, load_csv, load_json
from chunking import chunk_text
from pii import redact_pii

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "meridian_documents"
PERSIST_DIR = "./chroma_store"

# TODO 2:
# Leave Policy PDF contains clear numbered sections such as
# "1. Scope", "2. Annual Leave Entitlement", etc.
# Heading-aware chunking keeps each policy section together
# instead of arbitrarily splitting it by character count.
CHUNK_STRATEGY = "heading_aware"


def build():
    print("=" * 64)
    print("Meridian Freight & Logistics — Building the Knowledge Base")
    print(f"Chunking strategy in use: {CHUNK_STRATEGY}")
    print("=" * 64)

    filepaths = sorted(glob.glob("../documents/*"))

    all_documents = []
    total_pii_redactions = {}

    for filepath in filepaths:
        filename = os.path.basename(filepath)
        print(f"\nProcessing {filename} ...")

        # ==========================================================
        # TODO 4: Call the correct loader for each file type
        # ==========================================================

        extension = os.path.splitext(filename)[1].lower()

        if extension == ".pdf":
            raw_units = load_pdf(filepath)

        elif extension in [".html", ".htm"]:
            raw_units = load_html(filepath)

        elif extension == ".csv":
            # Each CSV row is already a complete business record.
            raw_units = load_csv(
                filepath,
                id_column="location_code"
            )

        elif extension == ".json":
            # The open positions records are stored under
            # the "open_positions" top-level key.
            raw_units = load_json(
                filepath,
                list_key="open_positions"
            )

        else:
            print(f"Skipping unsupported file type: {filename}")
            continue

        # ==========================================================
        # Process each loaded unit
        # ==========================================================

        chunk_index = 0

        for unit in raw_units:

            original_text = unit["text"]

            # ======================================================
            # TODO 5: Redact PII BEFORE chunking
            # ======================================================
            #
            # This ensures sensitive information is removed before
            # the text is split and embedded into the vector store.

            redacted_text, pii_counts = redact_pii(original_text)

            for pii_type, count in pii_counts.items():
                total_pii_redactions[pii_type] = (
                    total_pii_redactions.get(pii_type, 0) + count
                )

            # ======================================================
            # TODO 6: Chunk appropriately
            # ======================================================

            if extension == ".csv":

                # CSV rows represent complete business facts.
                # Keep each row as one chunk so fields such as
                # location, role band, min pay and max pay stay
                # together.
                chunks = [redacted_text]

            else:

                chunks = chunk_text(
                    redacted_text,
                    strategy=CHUNK_STRATEGY
                )

            # ======================================================
            # TODO 7: Attach metadata
            # ======================================================

            for chunk in chunks:

                metadata = dict(unit.get("metadata", {}))

                metadata["source"] = filename
                metadata["chunk_index"] = chunk_index

                # Compliance needs exact document traceability.
                metadata["document_id"] = ""
                metadata["version"] = ""
                metadata["effective_date"] = ""

                # --------------------------------------------------
                # Extract document metadata when it appears in text.
                # Handles formats such as:
                #
                # Document ID: MFL-HR-POL-04
                # Version: 4.0
                # Effective Date: 1 July 2026
                #
                # and the HTML header format where these fields
                # appear on the same line.
                # --------------------------------------------------

                document_id_match = re.search(
                    r"Document ID\s*[:=]\s*([^,\n]+)",
                    original_text,
                    re.IGNORECASE
                )

                version_match = re.search(
                    r"Version\s*[:=]\s*([^,\n]+)",
                    original_text,
                    re.IGNORECASE
                )

                effective_date_match = re.search(
                    r"Effective Date\s*[:=]\s*([^,\n]+)",
                    original_text,
                    re.IGNORECASE
                )

                if document_id_match:
                    metadata["document_id"] = (
                        document_id_match.group(1).strip()
                    )

                if version_match:
                    metadata["version"] = (
                        version_match.group(1).strip()
                    )

                if effective_date_match:
                    metadata["effective_date"] = (
                        effective_date_match.group(1).strip()
                    )

                all_documents.append(
                    Document(
                        page_content=chunk,
                        metadata=metadata
                    )
                )

                chunk_index += 1

    # ==============================================================
    # Summary
    # ==============================================================

    print(f"\nTotal chunks to embed: {len(all_documents)}")

    if total_pii_redactions:
        print(f"PII redacted at ingest: {total_pii_redactions}")
    else:
        print("No PII detected during ingest.")

    # ==============================================================
    # TODO 8: Embed and store in ChromaDB
    # ==============================================================

    embeddings = OpenAIEmbeddings(
        model=EMBED_MODEL
    )

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR
    )

    vectorstore.add_documents(all_documents)

    print(f"Stored {len(all_documents)} chunks in ChromaDB.")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Persist directory: {PERSIST_DIR}")

    print("\nBuild complete. Next: fill in ../starter/app.py")


if __name__ == "__main__":
    build()
"""
metadata_enrichment.py

Prastav — Metadata Enrichment: doc_type, version, effective_date, source
=========================================================================
Adds document-level metadata to every chunk. For CSV (which has no natural
document version), a derived version/effective_date is computed from rows.
"""
import re
import csv
import json
import os

# Matches: "... Version: 3.2  |  Effective Date: 15 March 2026 | ..."
# Works whether Version/Effective Date are adjacent or separated by other
# fields, as long as Version appears before Effective Date on the line.
HEADER_PATTERN = re.compile(
    r"Version:\s*([\w.]+).*?Effective Date:\s*([^\n|]+?)(?:\s*\||\s*$)",
    re.IGNORECASE,
)


def infer_doc_type(filename: str) -> str:
    """Infer the document type from canonical Prastav filenames."""
    name = filename.lower()
    if "capability" in name:
        return "Capability Statement"
    if "case_study" in name:
        return "Client Case Study"
    if "sales_faq" in name or "playbook" in name:
        return "Sales FAQ"
    if "win_loss" in name:
        return "RFP Win/Loss Log"
    if "service_catalogue" in name:
        return "Service Catalogue"
    return "Unknown"


def enrich_from_text(text: str, filename: str) -> dict:
    """For PDF / Word / HTML sources: look for a 'Version: X ... Effective
    Date: Y' style header line, common to every document template used
    in this lab."""
    match = HEADER_PATTERN.search(text)
    version = match.group(1).strip() if match else "Unknown"
    effective_date = match.group(2).strip() if match else "Unknown"
    return {
        "doc_type": infer_doc_type(filename),
        "version": version,
        "effective_date": effective_date,
    }


def enrich_from_json(filepath: str) -> dict:
    """JSON documents state these fields as real keys — no regex needed."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "doc_type": infer_doc_type(os.path.basename(filepath)),
        "version": data.get("version", "Unknown"),
        "effective_date": data.get("effective_date", "Unknown"),
    }


def enrich_from_csv(filepath: str) -> dict:
    """Derive metadata from row-level dates when no document version exists."""
    latest_submission = None
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            submitted = row.get("submission_date")
            if submitted and (latest_submission is None or submitted > latest_submission):
                latest_submission = submitted
    return {
        "doc_type": infer_doc_type(os.path.basename(filepath)),
        "version": "Derived-from-latest-submission-date",
        "effective_date": latest_submission or "Unknown",
    }


def enrich_document(filepath: str, sample_text: str = "") -> dict:
    """Single entry point — dispatches by file extension.
    `sample_text` is only needed for pdf/docx/html (pass the first loaded
    unit's text); json and csv read the file directly."""
    filename = os.path.basename(filepath)
    ext = filepath.rsplit(".", 1)[-1].lower()

    if ext == "json":
        return enrich_from_json(filepath)
    if ext == "csv":
        return enrich_from_csv(filepath)
    return enrich_from_text(sample_text, filename)

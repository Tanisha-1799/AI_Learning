"""
loaders.py

Prastav — Multi-Format Document Loaders
======================================
Each function returns plain dicts in a common shape:
{"text": <string>, "metadata": {"source": <filename>, ...}}

This keeps ingestion format-agnostic downstream. Chunking, embedding,
hybrid retrieval, and reranking only need text plus source metadata.
"""
import csv
import json
import os
import pymupdf as fitz  # PyMuPDF
import docx  # python-docx
from bs4 import BeautifulSoup


def load_pdf(filepath: str) -> list[dict]:
    """One 'document' per page — keeps citations pointing at a specific page."""
    docs = []
    filename = os.path.basename(filepath)
    pdf = fitz.open(filepath)
    for page_num, page in enumerate(pdf, start=1):
        text = page.get_text().strip()
        if text:
            docs.append({
                "text": text,
                "metadata": {"source": filename, "page": page_num},
            })
    pdf.close()
    return docs


def load_docx(filepath: str) -> list[dict]:
    """One 'document' for the whole file — Word docs here are short enough
    that page-level splitting isn't meaningful; chunking handles the rest."""
    d = docx.Document(filepath)
    full_text = "\n".join(p.text for p in d.paragraphs if p.text.strip())
    return [{
        "text": full_text,
        "metadata": {"source": os.path.basename(filepath)},
    }]


def load_html(filepath: str) -> list[dict]:
    """One 'document' per <h2> section — HTML FAQs are naturally structured
    this way, so splitting at headings keeps each Q&A pair intact."""
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    docs = []
    filename = os.path.basename(filepath)

    # Grab the intro paragraph (document id/version line) as its own chunk.
    intro = soup.find("p")
    if intro:
        docs.append({"text": intro.get_text(strip=True),
                      "metadata": {"source": filename, "section": "header"}})

    for heading in soup.find_all("h2"):
        section_title = heading.get_text(strip=True)
        paragraph = heading.find_next_sibling("p")
        section_text = paragraph.get_text(strip=True) if paragraph else ""
        docs.append({
            "text": f"{section_title}\n{section_text}",
            "metadata": {"source": filename, "section": section_title},
        })
    return docs


def load_csv(filepath: str) -> list[dict]:
    """One document per RFP log row."""
    docs = []
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = ", ".join(f"{key}: {value}" for key, value in row.items())
            docs.append({
                "text": text,
                "metadata": {"source": filename, "row_id": row.get("rfp_id", "")},
            })
    return docs


def load_json(filepath: str) -> list[dict]:
    """One document per service entry in the catalogue."""
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    docs = []
    records = data.get("services", [])
    for record in records:
        text = ", ".join(f"{key}: {value}" for key, value in record.items())
        docs.append({
            "text": text,
            "metadata": {
                "source": filename,
                "service_name": record.get("service_name", ""),
                "category": record.get("category", ""),
            },
        })
    return docs


# Dispatch table: pick the right loader based on file extension.
LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".html": load_html,
    ".csv": load_csv,
    ".json": load_json,
}


def load_document(filepath: str) -> list[dict]:
    """Single entry point — figures out which loader to use from the extension."""
    ext = "." + filepath.rsplit(".", 1)[-1].lower()
    if ext not in LOADERS:
        raise ValueError(f"No loader registered for file type: {ext}")
    return LOADERS[ext](filepath)

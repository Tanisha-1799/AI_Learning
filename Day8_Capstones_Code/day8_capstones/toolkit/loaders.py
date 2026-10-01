"""
toolkit/loaders.py

Multi-format document loaders. Each function takes a file path and
returns a list of {"text": ..., "metadata": {"source": ..., ...}} dicts —
one common shape regardless of original file format.
"""
import csv
import json
import docx  # python-docx
from bs4 import BeautifulSoup


def load_pdf(filepath: str) -> list[dict]:
    import fitz  # PyMuPDF — imported here so this is the only loader that needs it installed
    docs = []
    pdf = fitz.open(filepath)
    for page_num, page in enumerate(pdf, start=1):
        text = page.get_text().strip()
        if text:
            docs.append({"text": text, "metadata": {"source": filepath.split("/")[-1], "page": page_num}})
    pdf.close()
    return docs


def load_docx(filepath: str) -> list[dict]:
    d = docx.Document(filepath)
    full_text = "\n".join(p.text for p in d.paragraphs if p.text.strip())
    return [{"text": full_text, "metadata": {"source": filepath.split("/")[-1]}}]


def load_html(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    docs = []
    filename = filepath.split("/")[-1]
    intro = soup.find("p")
    if intro:
        docs.append({"text": intro.get_text(strip=True), "metadata": {"source": filename, "section": "header"}})
    for heading in soup.find_all("h2"):
        section_title = heading.get_text(strip=True)
        paragraph = heading.find_next_sibling("p")
        section_text = paragraph.get_text(strip=True) if paragraph else ""
        docs.append({"text": f"{section_title}\n{section_text}", "metadata": {"source": filename, "section": section_title}})
    return docs


def load_csv(filepath: str, id_column: str = None) -> list[dict]:
    docs = []
    filename = filepath.split("/")[-1]
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = ", ".join(f"{key}: {value}" for key, value in row.items())
            row_id = row.get(id_column, "") if id_column else ""
            docs.append({"text": text, "metadata": {"source": filename, "row_id": row_id}})
    return docs


def load_json(filepath: str, list_key: str) -> list[dict]:
    """list_key: the top-level key in the JSON file holding the list of
    records to turn into documents (varies per file — pass it explicitly)."""
    filename = filepath.split("/")[-1]
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    docs = []
    records = data.get(list_key, [])
    for record in records:
        text = ", ".join(f"{key}: {value}" for key, value in record.items())
        docs.append({"text": text, "metadata": {"source": filename}})
    return docs

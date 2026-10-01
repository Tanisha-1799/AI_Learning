"""
toolkit/chunking.py

Five chunking strategies, all callable through one entry point:
    chunk_text(text, strategy="overlap")
"""
import re


def fixed_chunk(text: str, chunk_size: int = 500) -> list[str]:
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    return [c.strip() for c in chunks if c.strip()]


def overlap_chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def sentence_chunk(text: str, max_sentences: int = 4) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s for s in sentences if s]
    chunks = []
    for i in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[i:i + max_sentences])
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks


def heading_aware_chunk(text: str) -> list[str]:
    """Splits at numbered headings ('1. Scope') OR labelled clauses/
    sections ('Clause 4:', 'Section 2:', 'Q3:') — falls back to semantic
    (paragraph) chunking if no headings are found."""
    heading_pattern = re.compile(
        r"^\s*(\d+\.\s+[A-Z].{0,80}|(?:Clause|Section|Q)\s*\d+[:.].{0,80})\s*$",
        re.MULTILINE,
    )
    matches = list(heading_pattern.finditer(text))
    if not matches:
        return semantic_chunk(text)
    chunks = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        if section:
            chunks.append(section)
    return chunks


def semantic_chunk(text: str) -> list[str]:
    """Approximated via paragraph (blank-line) splitting — not true
    embedding-based semantic chunking. See Day 1's caveat on this."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


STRATEGIES = {
    "fixed": fixed_chunk,
    "overlap": overlap_chunk,
    "sentence": sentence_chunk,
    "heading_aware": heading_aware_chunk,
    "semantic": semantic_chunk,
}


def chunk_text(text: str, strategy: str = "overlap", **kwargs) -> list[str]:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown chunking strategy: {strategy}. Choose from: {list(STRATEGIES.keys())}")
    return STRATEGIES[strategy](text, **kwargs)

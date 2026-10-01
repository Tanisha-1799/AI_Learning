"""Chunking utilities for Prastav (fixed overlap strategy)."""


def overlap_chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Fixed-size chunks that share `overlap` characters with the next
    one, so an idea sitting on a chunk boundary isn't lost entirely."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        if end >= len(text):
            break
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Single entry point, kept for consistency with Disha's interface."""
    return overlap_chunk(text, chunk_size=chunk_size, overlap=overlap)

"""Cross-encoder reranking for Prastav hybrid retrieval candidates."""
from sentence_transformers import CrossEncoder

# A small, fast, well-established cross-encoder for this kind of reranking.
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_model = None
_load_error = None


def _get_model():
    """Lazy-load the model once, the first time it's actually needed —
    downloading/loading it on import would slow down every script that
    imports this module, even ones that never call rerank()."""
    global _model, _load_error
    if _model is None:
        if _load_error is not None:
            raise RuntimeError(f"Reranker unavailable: {_load_error}")
        try:
            _model = CrossEncoder(CROSS_ENCODER_MODEL)
        except Exception as exc:
            _load_error = exc
            raise RuntimeError(f"Reranker initialization failed: {exc}") from exc
    return _model


def rerank(query: str, candidates: list, top_k: int = 3) -> list:
    """
    candidates: a list of (Document, fusion_score) pairs from hybrid_retrieval.
    Returns the top_k candidates re-scored and re-sorted by the cross-encoder,
    as a list of (Document, cross_encoder_score) pairs.
    """
    if not candidates:
        return []

    model = _get_model()
    pairs = [[query, doc.page_content] for doc, _ in candidates]
    cross_scores = model.predict(pairs)

    scored = list(zip([doc for doc, _ in candidates], cross_scores))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]

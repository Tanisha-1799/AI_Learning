"""
toolkit/reranking.py

Cross-encoder reranking, applied AFTER hybrid/vector retrieval narrows
the field. Use when result ORDER quality matters more than raw speed.
"""
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder(CROSS_ENCODER_MODEL)
    return _model


def rerank(query: str, candidates: list, top_k: int = 3) -> list:
    if not candidates:
        return []
    model = _get_model()
    pairs = [[query, doc.page_content] for doc, _ in candidates]
    cross_scores = model.predict(pairs)
    scored = list(zip([doc for doc, _ in candidates], cross_scores))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]

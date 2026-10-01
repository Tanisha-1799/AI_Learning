"""Hybrid retrieval for Prastav: weighted BM25 + vector fusion."""
import re

from rank_bm25 import BM25Okapi


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in",
    "is", "it", "of", "on", "or", "our", "that", "the", "to", "we", "what", "when",
    "where", "which", "who", "with", "you", "your",
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class HybridIndex:
    """Wraps a Chroma vectorstore with a parallel BM25 keyword index over
    the SAME chunks, so both can be queried and fused together."""

    def __init__(self, vectorstore, all_documents: list):
        """
        vectorstore: a LangChain Chroma vectorstore (already built and populated)
        all_documents: the same list of langchain_core.documents.Document
                        objects that were embedded into vectorstore — needed
                        so BM25 can be built over identical chunks/ids
        """
        self.vectorstore = vectorstore
        self.documents = all_documents
        tokenized = [_tokenize(doc.page_content) for doc in all_documents]
        self.bm25 = BM25Okapi(tokenized)

    def _bm25_rank(self, query: str, top_n: int) -> list:
        """Returns top_n (Document, BM25 score) pairs, best first."""
        tokenized_query = _tokenize(query)
        if not tokenized_query:
            return []
        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [(self.documents[i], float(scores[i])) for i in ranked_indices[:top_n]]

    def _vector_rank(self, query: str, top_n: int) -> list:
        """Returns top_n (Document, vector score) pairs, best first."""
        try:
            results = self.vectorstore.similarity_search_with_relevance_scores(query, k=top_n)
            return [(doc, float(score)) for doc, score in results]
        except Exception:
            # Fallback for backends that do not provide relevance scores.
            docs = self.vectorstore.similarity_search(query, k=top_n)
            return [(doc, float(top_n - rank)) for rank, doc in enumerate(docs)]

    def _metadata_hint_score(self, query_tokens: set[str], doc) -> float:
        """Small lexical prior from metadata/doc labels to break close ties."""
        md = doc.metadata or {}
        hint_text = " ".join(
            [
                str(md.get("doc_type", "")),
                str(md.get("source", "")),
                str(md.get("service_name", "")),
                str(md.get("section", "")),
            ]
        ).replace("_", " ")
        hint_tokens = set(_tokenize(hint_text))
        if not hint_tokens or not query_tokens:
            return 0.0
        overlap = len(query_tokens & hint_tokens)
        return min(0.2, overlap * 0.05)

    def hybrid_search(self, query: str, k: int = 5, fetch_n: int = 15) -> list:
        """Run BM25 + vector retrieval and fuse with weighted normalized scores."""
        bm25_results = self._bm25_rank(query, fetch_n)
        vector_results = self._vector_rank(query, fetch_n)

        bm25_max = max((score for _, score in bm25_results), default=0.0)
        vector_max = max((score for _, score in vector_results), default=0.0)

        scores = {}
        docs_by_key = {}
        query_tokens = set(_tokenize(query))

        def doc_key(doc):
            # Chunks are uniquely identified by source + chunk_index.
            return (doc.metadata.get("source"), doc.metadata.get("chunk_index"))

        for doc, raw_score in bm25_results:
            key = doc_key(doc)
            norm = (raw_score / bm25_max) if bm25_max > 0 else 0.0
            scores[key] = scores.get(key, 0.0) + (0.65 * norm)
            docs_by_key[key] = doc

        for doc, raw_score in vector_results:
            key = doc_key(doc)
            norm = (raw_score / vector_max) if vector_max > 0 else 0.0
            scores[key] = scores.get(key, 0.0) + (0.35 * norm)
            docs_by_key[key] = doc

        for key, doc in docs_by_key.items():
            scores[key] += self._metadata_hint_score(query_tokens, doc)

        ranked_keys = sorted(scores.keys(), key=lambda key: scores[key], reverse=True)
        return [(docs_by_key[key], scores[key]) for key in ranked_keys[:k]]

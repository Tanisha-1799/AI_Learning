"""
toolkit/hybrid_retrieval.py

Hybrid retrieval: BM25 (keyword) + vector search, fused with Reciprocal
Rank Fusion (RRF). Use this when exact terms (IDs, codes, clause
numbers) matter alongside semantic meaning.
"""
from rank_bm25 import BM25Okapi


class HybridIndex:
    def __init__(self, vectorstore, all_documents: list):
        self.vectorstore = vectorstore
        self.documents = all_documents
        tokenized = [doc.page_content.lower().split() for doc in all_documents]
        self.bm25 = BM25Okapi(tokenized)

    def _bm25_rank(self, query: str, top_n: int) -> list:
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.documents[i] for i in ranked_indices[:top_n]]

    def _vector_rank(self, query: str, top_n: int) -> list:
        return self.vectorstore.similarity_search(query, k=top_n)

    def hybrid_search(self, query: str, k: int = 5, fetch_n: int = 15, rrf_k: int = 60) -> list:
        bm25_results = self._bm25_rank(query, fetch_n)
        vector_results = self._vector_rank(query, fetch_n)

        scores = {}
        docs_by_key = {}

        def doc_key(doc):
            return (doc.metadata.get("source"), doc.metadata.get("chunk_index"))

        for rank, doc in enumerate(bm25_results):
            key = doc_key(doc)
            scores[key] = scores.get(key, 0) + 1 / (rrf_k + rank + 1)
            docs_by_key[key] = doc

        for rank, doc in enumerate(vector_results):
            key = doc_key(doc)
            scores[key] = scores.get(key, 0) + 1 / (rrf_k + rank + 1)
            docs_by_key[key] = doc

        ranked_keys = sorted(scores.keys(), key=lambda key: scores[key], reverse=True)
        return [(docs_by_key[key], scores[key]) for key in ranked_keys[:k]]

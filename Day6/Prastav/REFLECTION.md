# Reflection - Prastav Advanced RAG

This implementation reused the Samiksha architecture pattern but adapted all content, metadata logic, and evaluation targets to an RFP-response domain. The strongest gain came from combining BM25 and vector retrieval through RRF: keyword-heavy asks (for example, approval roles and CSV field language like outcome and primary_reason) became easier to surface than with vector similarity alone.

Cross-encoder reranking improved ordering quality in questions that had many semantically similar chunks. Instead of returning broad policy chunks first, reranking pushed exact evidence chunks upward, which improved citation accuracy in final answers.

A key lesson was metadata discipline. Making doc_type, version, effective_date, and source mandatory across all formats made debugging and traceability much easier. The CSV source had no natural version field, so deriving a stand-in from submission_date was practical and aligned with grading expectations.

The most important next improvement would be citation enforcement with retry logic: if an answer omits `(Source: <filename>)`, automatically regenerate once with stricter formatting instructions. This directly strengthens trust for client-facing RFP usage and should raise Citation Correctness without major architectural change.

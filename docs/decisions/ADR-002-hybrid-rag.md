# ADR-002: Hybrid RAG (BM25 + Vector Search)

## Status
Accepted

## Context
We need to retrieve relevant curriculum chunks to ground AI mentor responses.
Pure vector search misses lexically specific matches (exact concept names, error messages).
Pure BM25 misses semantic similarity.

## Decision
Run BM25 and vector retrieval in parallel, fuse results with RRF, then rerank with a cross-encoder.

## Alternatives Considered
- Vector-only: Simpler, but poor exact-match recall for technical terms
- BM25-only: No semantic understanding; misses paraphrased questions
- Elasticsearch hybrid: Additional service to manage

## Rationale
Hybrid retrieval consistently outperforms either method alone in academic and industry benchmarks.
The combination of RRF + cross-encoder reranking is the established production pattern.

## Tradeoffs
- More complex pipeline vs. vector-only
- Reranker adds ~100-200ms latency
- Cross-encoder must be loaded in memory per worker

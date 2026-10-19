# ADR-004: Cross-Encoder for Reranking

## Status
Accepted

## Context
After RRF fusion we have ~20-50 candidates. We need to select the best 5 for the LLM context.
A cross-encoder sees both query and passage simultaneously, enabling much more accurate scoring.

## Decision
Use sentence-transformers cross-encoder/ms-marco-MiniLM-L-6-v2 as the reranker.

## Alternatives Considered
- ColBERT: Higher quality but significantly more complex to deploy
- GPT-4o-mini as reranker: Expensive, adds 500ms+ latency
- No reranker: Lower answer quality; RRF ranking alone often incorrect for complex queries

## Rationale
ms-marco-MiniLM-L-6-v2 is a well-benchmarked, production-tested model with excellent
speed/accuracy tradeoff. Runs on CPU in ~100-200ms for 50 candidates.

## Tradeoffs
- Adds ~150ms latency per request
- Requires model to be loaded in worker memory (~60MB)
- If model fails to load, system falls back to RRF ranking

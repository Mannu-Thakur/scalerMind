# ADR-003: Reciprocal Rank Fusion for Hybrid Search

## Status
Accepted

## Context
After retrieving candidates from BM25 and vector search, we need to merge two ranked lists
into a single ordering before reranking.

## Decision
Use Reciprocal Rank Fusion (RRF) with k=60 (canonical default from Cormack et al. 2009).

## Alternatives Considered
- Score normalization (min-max, z-score): BM25 and cosine scores are not comparable
- Linear combination: Requires tuned weights; fragile across query types
- CombSUM / CombMNZ: Historical alternatives; RRF outperforms in practice

## Rationale
RRF is parameter-free (aside from k), rank-based (scores don't need to be comparable),
and empirically robust. k=60 is the standard default that works well without tuning.

## Tradeoffs
- k can be tuned on held-out evaluation data for marginal gains
- RRF output scores are not interpretable as relevance scores

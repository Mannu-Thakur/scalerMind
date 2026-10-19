# ADR-001: PostgreSQL as Primary Database

## Status
Accepted

## Context
We need a relational database for transactional data (users, conversations, submissions, events)
and a vector store for embedding-based retrieval.

## Decision
Use PostgreSQL 16 with the pgvector extension.

## Alternatives Considered
- MySQL: Lacks pgvector; fewer advanced indexing options
- MongoDB: Document store would lose relational integrity; no native vector support
- Separate vector DB (Qdrant + SQLite): Two systems to operate, no ACID across them

## Rationale
- pgvector allows vector search within the same database, eliminating a separate vector store
- Familiar SQL tooling for analytics queries
- RDS managed service on AWS reduces operational burden
- ACID compliance required for financial/event data

## Tradeoffs
- pgvector IVFFlat/HNSW index is slower than dedicated vector DBs at 100M+ vectors
- Single point of failure if not configured Multi-AZ
- Mitigation: Start with pgvector; migrate chunks to Qdrant if p99 exceeds SLA

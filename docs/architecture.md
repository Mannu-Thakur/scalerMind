# ScalerMind — System Architecture

## Overview

ScalerMind is an AI-native learning platform for computer science students. It combines
curriculum-grounded AI mentoring, intelligent code review, natural-language analytics,
and adaptive personalization into a cohesive product.

---

## High-Level System Diagram

```
                          ┌─────────────────────┐
                          │  React / TypeScript  │
                          │       Frontend       │
                          └──────────┬───────────┘
                                     │ HTTPS / SSE
                          ┌──────────▼────────────┐
                          │   Load Balancer (ALB)  │
                          └──────────┬────────────┘
                                     │
                ┌────────────────────▼─────────────────────┐
                │              FastAPI  (API)               │
                │  Auth │ Mentor │ Code Review │ Analytics  │
                └──┬───────────────────────────────────┬───┘
                   │                                   │
        ┌──────────▼──────────┐          ┌────────────▼──────────┐
        │  PostgreSQL  (RDS)  │          │   Redis (ElastiCache)  │
        │  + pgvector         │          │  Cache / job state     │
        └─────────────────────┘          └───────────────────────┘
                   │
        ┌──────────▼───────────────────────────────────┐
        │         Celery Workers (ECS Tasks)            │
        │  • Document ingestion / embedding             │
        │  • Code execution sandbox                     │
        │  • Evaluation runs                            │
        └──────────────────────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  S3 (docs, logs)    │
        └─────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | Fast dev, strong typing, SSE support |
| State | Zustand + TanStack Query | Lightweight, composable, excellent async |
| Styling | Tailwind CSS + shadcn/ui | Rapid consistent UI, no heavy framework lock-in |
| Code Editor | CodeMirror 6 | Language-aware, React-friendly, extensible |
| Backend | FastAPI (Python 3.12) | Native async, Pydantic v2, OpenAPI docs |
| ORM | SQLAlchemy 2.0 (async) + asyncpg | Type-safe, async-first, migration-friendly |
| Migrations | Alembic | Industry standard |
| Database | PostgreSQL 16 + pgvector | Relational + vector in one store |
| Cache / Queue | Redis 7 | Job state, pub/sub, rate limiting, caching |
| Task Queue | Celery 5 | Mature, Redis-backed, retry logic |
| BM25 | rank-bm25 (in-process) | Pure Python, no extra service |
| Embeddings | OpenAI text-embedding-3-small | High quality, cheap, batch API |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 | Fast, accurate, runs locally |
| LLM | OpenAI GPT-4o-mini (default), GPT-4o (complex tasks) | Cost-effective, streaming, function calling |
| Auth | JWT (PyJWT) + bcrypt | Short-lived access tokens, rotating refresh sessions, role-based |
| CI | GitHub Actions | Lint → typecheck → test → build |
| Deployment | AWS ECS Fargate + RDS + ElastiCache + S3 | Serverless containers, managed services |
| Local Dev | Docker Compose | One-command setup |

---

## Core Data Flows

### Flow A — AI Mentor with Hybrid RAG

```
User Message
     ↓
FastAPI POST /api/mentor/chat
     ↓
Auth middleware → user_id, role
     ↓
Rate limiter (Redis)
     ↓
Learner context retrieval (Redis cache → PostgreSQL)
     ↓
Query understanding (lightweight LLM call)
     ↓
Hybrid Retrieval (parallel):
  ├── BM25 (rank-bm25, in-memory index)
  └── Vector Search (pgvector cosine similarity)
     ↓
RRF Fusion: score(d) = Σ 1/(k + rank_i(d))  [k=60]
     ↓
Cross-Encoder Reranker (top-N of fused list)
     ↓
Context Builder (chunks + citation markers [1][2]...)
     ↓
LLM (streaming SSE)
     ↓
Citation validation
     ↓
Persist conversation + message + learning event
```

### Flow B — Code Review Agent

```
POST /api/code-review
     ↓
Validate + store submission
     ↓
Enqueue Celery task → return {job_id}
     ↓
Worker: CodeReviewOrchestrator
  Step 1: Code Parser (language detection + AST)
  Step 2: Static Analysis (deterministic rules)
  Step 3: Complexity Analysis (AST-based Big-O)
  Step 4: Test Generation (LLM → structured JSON)
  Step 5: Sandbox Execution (subprocess + resource limits)
  Step 6: Failure Analysis (compare actual vs expected output)
  Step 7: LLM Reviewer (structured JSON output with schema)
  Step 8: Persist findings
     ↓
SSE progress events → frontend (Redis pub/sub)
     ↓
Structured review result displayed
```

### Flow C — Natural Language Analytics

```
POST /api/analytics/query
     ↓
Auth (learner sees own data; admin sees all)
     ↓
Schema context (cached in Redis)
     ↓
LLM SQL generation
     ↓
SQL Validator (deterministic):
  • Only SELECT allowed
  • Block: INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE
  • Parse with sqlparse
  • Reject multi-statement queries
  • Inject LIMIT if missing
     ↓
Read-only DB connection (restricted PostgreSQL user)
     ↓
Execute with 5s timeout
     ↓
Result normalization
     ↓
LLM explanation
```

### Flow D — Personalized Mentor

```
User session begins
     ↓
Load learner profile (Redis cache → PostgreSQL)
  • topic_performance: {topic_id → {score, attempts, last_seen}}
  • weak_areas: [topic_ids]
  • skill_level: beginner | intermediate | advanced
     ↓
Mentor agent selects response style:
  beginner  → concept + analogy + simple example + hint
  advanced  → invariant + complexity + optimization + edge cases
     ↓
Injected as system context before RAG retrieval
```

---

## RAG Architecture

### Ingestion

```
Raw Document (PDF / Markdown / HTML)
     ↓
Parser (pypdf2 / python-markdown / beautifulsoup4)
     ↓
Cleaner (strip boilerplate, normalize whitespace)
     ↓
Chunker (sliding window, configurable size + overlap)
     ↓
Metadata Extractor
  {document_id, course, module, topic, lesson,
   section, page, chunk_id, source_url, created_at}
     ↓
Embedding (OpenAI text-embedding-3-small, batched)
     ↓
PostgreSQL: document_chunks (text + vector)
BM25 index: rebuilt from document_chunks
S3: raw documents archived
```

### Configuration (all configurable via env vars)

```
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=64
RAG_TOP_K=10
RAG_RERANK_TOP_N=5
RAG_RRF_K=60
RAG_SIMILARITY_THRESHOLD=0.7
```

---

## Agent Architecture

```
RouterAgent
  ├── MentorAgent
  │     tools: search_curriculum, retrieve_learner_context, get_topic_performance
  │     max_steps: 5  |  timeout: 30s
  │     output: MentorResponse
  │
  ├── CodeReviewAgent
  │     tools: run_static_analysis, generate_tests, run_code, analyze_failures
  │     max_steps: 8  |  timeout: 120s
  │     output: CodeReviewResult
  │
  └── AnalyticsAgent
        tools: get_schema, generate_sql, execute_safe_sql
        max_steps: 4  |  timeout: 20s
        output: AnalyticsResult
```

---

## Security Model

| Concern | Mitigation |
|---|---|
| Authentication | JWT HS256, 15-min access + 7-day refresh |
| Authorization | Role-based (learner/admin), server-enforced |
| SQL injection | ORM parameterized + sqlparse validation for NL-SQL |
| Code execution | subprocess isolation, CPU/memory/time limits |
| Prompt injection | Retrieved content in user-role messages, not system |
| Rate limiting | Redis sliding window per user per endpoint |
| Secrets | Env vars only, never committed |
| CORS | Explicit origin allowlist |
| Input validation | Pydantic v2 strict models |
| LLM output validation | JSON schema validation on structured outputs |

### Authentication implementation

Access tokens are signed with HS256 and contain issuer, audience, type, subject, JTI, issue time, and expiration claims. The API returns the 15-minute access token in the JSON response for in-memory browser use. Refresh tokens live for 7 days, are held in an HttpOnly cookie, and are stored in PostgreSQL only as SHA-256 hashes. Each refresh rotates the token in its session family; replaying a revoked token revokes the remaining active sessions in that family. Refresh and logout requests require a double-submit CSRF cookie/header pair. Signup always assigns `learner`; admin role assignment is reserved for privileged provisioning.

Production settings require an explicit JWT secret of at least 32 characters and secure cookies. Local development can omit the JWT secret, in which case each API process uses a random key; sessions therefore do not survive API restarts until a stable local secret is configured.

---

## Scaling Strategy

| Component | Horizontal Scale | Notes |
|---|---|---|
| FastAPI | ECS auto-scaling (CPU/RPS) | Stateless |
| Celery Workers | ECS auto-scaling (queue depth) | Code exec workers isolated |
| PostgreSQL | RDS Multi-AZ, read replicas | PgBouncer connection pooling |
| Redis | ElastiCache cluster mode | |
| BM25 index | In-memory per worker | Rebuilt on deploy (<1M chunks: fine) |
| Vector Search | pgvector IVFFlat index | Re-index after bulk ingestion |

---

## Failure Handling

| Dependency | Failure | Recovery |
|---|---|---|
| LLM API | Timeout / rate limit | Retry with exponential backoff, graceful error |
| Vector search | pgvector error | Fallback to BM25-only |
| BM25 | Index not loaded | Fallback to vector-only |
| Redis | Connection failure | Continue without cache, log warning |
| Reranker | Model load failure | Use RRF ranking directly |
| Sandbox | Code hangs | SIGKILL after timeout, report timeout error |
| Database | Connection failure | Pool retry, circuit breaker |

---

## Observability

Every request carries X-Request-ID (UUID4).

```json
{
  "request_id": "uuid",
  "user_id": "uuid",
  "endpoint": "POST /api/mentor/chat",
  "latency_ms": 1243,
  "llm_latency_ms": 890,
  "retrieval_latency_ms": 145,
  "reranker_latency_ms": 78,
  "tokens_prompt": 1240,
  "tokens_completion": 380,
  "cost_usd": 0.00042,
  "cache_hit": false,
  "retrieval_count": 5,
  "error": null
}
```

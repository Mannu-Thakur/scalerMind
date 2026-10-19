# ScalerMind — Project Plan

## Vision

Build a production-quality AI-native learning platform for CS students demonstrating
full-stack engineering, hybrid RAG, agentic workflows, evaluation infrastructure,
and AWS-ready deployment.

---

## Phases & Milestones

### PHASE 0 — Discovery & Architecture  ✅ (Current)

**Goal**: Define requirements, architecture, data flows, and tech stack.

**Deliverables**: architecture.md, requirements.md, decisions/, project-plan.md

**Acceptance**: Documents complete, risks identified, Phase 1 plan clear.


---

### PHASE 1 — Repository & Local Infrastructure

**Goal**: Monorepo skeleton, all services run via docker compose up.

**Deliverables**:

- Monorepo structure (apps/web, apps/api, apps/worker, ai/, db/, infrastructure/)
- React app (Vite + TypeScript) renders at localhost:3000
- FastAPI app responds at localhost:8000
- GET /health and GET /ready endpoints return 200
- PostgreSQL connected (SQLAlchemy pool verified)
- Redis connected (ping verified)
- Celery worker boots (heartbeat logged)
- docker-compose.yml, .env.example
- README with setup instructions

**Acceptance**: docker compose up → all 5 services healthy, health endpoints return 200.


---

### PHASE 2 — Authentication & Database

**Goal**: Real auth, real DB schema, protected routes.

**Deliverables**:

- Alembic migrations for: users, courses, lessons, topics, documents, document_chunks,
  conversations, messages, code_submissions, review_runs, test_cases, review_findings,
  learning_events, evaluation_datasets, evaluation_runs, evaluation_results, experiments
- JWT auth: signup, login, logout, refresh token
- Role-based access: learner, admin
- Protected API endpoints (FastAPI dependencies)
- React: login/signup pages, protected routes, token refresh
- Seed data: sample users, courses, topics
- Tests: auth endpoints, token validation, role enforcement, DB constraints

**Acceptance**: Login flow end-to-end. Protected routes reject unauthenticated requests.


---

### PHASE 3 — Basic Mentor (LLM, Streaming)

**Goal**: Working AI chat with streaming. No RAG yet.

**Deliverables**:

- POST /api/mentor/chat → SSE streaming response
- GET /api/mentor/conversations → list conversations
- Conversation persistence (PostgreSQL)
- React chat UI: streaming render, conversation list, message history
- LLM abstraction layer (OpenAIProvider, MockProvider)
- Prompt management (prompts/mentor/v1.txt)
- Error handling (LLM timeout, rate limit)
- Tests: streaming endpoint, persistence, error cases

**Acceptance**: User can chat with AI, responses stream, conversation survives refresh.


---

### PHASE 4 — Curriculum Ingestion

**Goal**: Document → chunks → embeddings → BM25 index → retrievable.

**Deliverables**:

- Ingestion CLI: python -m ai.rag.ingest ./data/curriculum
- Parser (PDF, Markdown)
- Chunker (sliding window, configurable)
- Metadata extraction
- OpenAI embedding (batched)
- PostgreSQL storage (document_chunks + pgvector)
- BM25 index build from DB
- Idempotent ingestion (dedup by hash)
- Sample curriculum seed data (DSA topics)
- Tests: chunking, metadata extraction, embedding storage, BM25 index

**Acceptance**: Ingest 10+ sample documents, verify retrieval returns relevant chunks.


---

### PHASE 5 — Hybrid RAG

**Goal**: BM25 + vector + RRF + reranker → grounded mentor answers with citations.

**Deliverables**:

- BM25 retrieval
- pgvector retrieval
- RRF fusion
- Cross-encoder reranker
- Context builder with citation markers
- Citation validation in responses
- RAG configuration via env vars
- Mentor upgraded to use RAG
- Tests: each retrieval component, RRF correctness, context construction

**Acceptance**: Mentor answers include citations referencing ingested documents.


---

### PHASE 6 — RAG Evaluation

**Goal**: Measurable retrieval and generation quality.

**Deliverables**:

- Evaluation dataset (50+ Q&A pairs with expected sources)
- Retrieval metrics: Recall@K, Precision@K, MRR, nDCG
- Generation metrics: faithfulness, answer correctness, context relevance
- Latency metrics: P50, P95, P99
- Cost tracking
- Evaluation API: POST /api/evaluations/run, GET /api/evaluations/:id
- Celery async evaluation jobs
- Versioned experiments (baseline vector vs hybrid vs reranked)
- Evaluation dashboard (React)
- Real experiment results

**Acceptance**: Run 3 experiments; dashboard shows real metric differences.


---

### PHASE 7 — Code Review Agent

**Goal**: Deterministic + LLM pipeline that reviews submitted code.

**Deliverables**:

- Code submission API
- Language detection
- Static analysis (Python: pyflakes/ast; C++: regex + pattern rules)
- Complexity analysis
- LLM test generation (structured JSON)
- Sandbox execution (subprocess, resource limits)
- Failure analysis
- LLM reviewer (structured output with schema validation)
- SSE progress events
- Code review UI
- Tests: each pipeline stage, structured output validation, timeout handling

**Acceptance**: Submit buggy binary search → receive structured review identifying the bug.


---

### PHASE 8 — Code Execution Hardening

**Goal**: Secure, isolated sandbox that survives malicious/hanging code.

**Deliverables**:

- CPU limit (RLIMIT_CPU)
- Memory limit (RLIMIT_AS)
- Output size limit
- Execution timeout (SIGKILL)
- Process group cleanup
- Celery job queue
- Tests: infinite loop → timeout; memory bomb → killed; normal code → correct output

**Acceptance**: Malicious/hanging code killed within timeout; API remains responsive.


---

### PHASE 9 — Analytics Agent (Text-to-SQL)

**Goal**: Natural language → safe SQL → explanation.

**Deliverables**:

- Schema retrieval (cached)
- SQL generation (LLM)
- SQL validator (sqlparse, allowlist)
- Read-only DB user
- Query execution (timeout + row limit)
- Result explanation
- Analytics UI
- Tests: SQL injection attempts, destructive queries rejected, valid queries succeed

**Acceptance**: "Which topic has the highest submission failure rate?" → correct SQL + answer.


---

### PHASE 10 — Personalization

**Goal**: Mentor adapts to learner history.

**Deliverables**:

- Learning event tracking
- Topic performance aggregation
- Skill level computation
- Learner context API
- Mentor system prompt adaptation
- Personalized response styles
- Tests: event recording, performance computation, prompt adaptation

**Acceptance**: Beginner user gets hints; advanced user gets complexity analysis.


---

### PHASE 11 — Observability & Performance

**Goal**: Full request tracing, cost tracking, metrics.

**Deliverables**:

- Request ID middleware
- Structured logging (JSON)
- Per-request cost/token tracking
- Latency measurements (retrieval, reranker, LLM)
- Redis cache metrics
- Profiling bottleneck report
- Optimization(s) with before/after measurements

**Acceptance**: Every log line has request_id; P95 latency measured and documented.


---

### PHASE 12 — AWS Deployment Architecture

**Goal**: Production-ready infrastructure definition.

**Deliverables**:

- infrastructure/aws/ with ECS task definitions, ALB config, RDS, ElastiCache
- IAM roles and policies
- CloudWatch log groups and alarms
- S3 bucket configuration
- Deployment runbook
- Secrets Manager integration

**Acceptance**: A new engineer can follow the runbook to deploy to AWS.


---

### PHASE 13 — CI/CD

**Goal**: Automated quality gates on every push.

**Deliverables**:

- GitHub Actions workflow
- Steps: install → lint → typecheck → unit tests → integration tests → build
- Status badges in README

**Acceptance**: CI passes on main; a broken commit fails CI.


---

### PHASE 14 — Final Hardening

**Goal**: Security, reliability, and code quality review.

**Deliverables**:

- Security audit (CORS, rate limits, auth, SQL safety, sandbox)
- Dead code removal
- Duplicate logic refactoring
- Complete test suite
- DB index audit
- API consistency review

---

### PHASE 15 — Product Polish

**Goal**: Product feels like a real startup application.

**Deliverables**:

- Landing page
- Dashboard improvements
- Skeleton/loading/empty/error states throughout
- Responsive layout
- Typography and spacing consistency

---

## Key Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| LLM API costs exceed budget | Medium | Use GPT-4o-mini by default, mock in tests |
| pgvector IVFFlat index slow at scale | Low | Pre-tune lists parameter; fallback to BM25 |
| Sandbox escape (untrusted code) | Medium | Resource limits + no network in subprocess |
| SQL injection via NL-SQL | Medium | sqlparse + restricted DB user + allowlist |
| BM25 memory at scale | Low | Acceptable at <1M chunks; can move to Elasticsearch |
| Reranker latency too high | Medium | Smaller model; cache top queries |
| Cross-encoder not available offline | Low | sentence-transformers downloads on first run |

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| API P95 latency (mentor) | < 2s (TTFB for streaming) |
| Code review P95 latency | < 30s |
| Database query P95 | < 100ms |
| Uptime (production) | 99.5% |
| Max concurrent users (local) | 10 |
| Authentication token validity | 15min access, 7day refresh |
| SQL query timeout | 5s |
| Code execution timeout | 10s |
| Max response body size | 10MB |

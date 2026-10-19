# ADR-005: Redis Usage

## Status
Accepted

## Context
Multiple platform features require fast ephemeral storage or pub/sub messaging
that should not go through the primary PostgreSQL database.

## Decision
Use Redis 7 for the following specific purposes:

| Purpose | Key Pattern | TTL |
|---|---|---|
| Rate limiting | ratelimit:{user_id}:{endpoint} | 60s window |
| Learner context cache | learner:{user_id}:context | 5 min |
| Schema cache for NL-SQL | nlsql:schema | 1 hour |
| Celery task results | celery-task-meta-{task_id} | 24 hours |
| Job progress events | job:{job_id}:progress | 2 hours |
| Revoked JWT jti | revoked:{jti} | = token remaining TTL |

## Alternatives Considered
- Memcached: No pub/sub, no data structures, no persistence
- Database for job state: Too much write pressure on primary DB
- In-process cache: Not shared across multiple API workers

## Tradeoffs
- Additional infrastructure component
- Cache invalidation complexity
- Failure behavior: if Redis is unavailable, rate limiting falls through (acceptable for MVP)
  and caches are bypassed (requests are slower but correct)

# ScalerMind

ScalerMind is an AI-assisted learning platform for computer science students. The repository contains a working local foundation and Phase 2 account authentication, protected API routes, and database schema.

## Start the local stack

Requirements: Docker Desktop with Docker Compose, and a browser. Node.js is only needed when running the frontend outside Docker.

1. Copy `.env.example` to `.env` if you want to change the local ports or database credentials. The checked-in defaults are for local development only.
2. From the repository root, run:

   ```sh
   docker compose up --build -d
   ```

3. Wait for the services to become healthy:

   ```sh
   docker compose ps
   ```

4. Open the frontend at <http://localhost:3000>. The API is at <http://localhost:8000>; its OpenAPI page is at <http://localhost:8000/docs>.

The API service applies Alembic migrations before it starts. New user signups receive the learner role; admin accounts are provisioned only through the optional local seed command. To add the sample course and topic, run `docker compose exec api python -m app.db.seed`. Optional demo users require `SEED_LEARNER_PASSWORD` or `SEED_ADMIN_PASSWORD` in your local `.env`; the sample file leaves both blank.

The API exposes `GET /health` as a liveness check and `GET /ready` as a dependency readiness check. `/ready` returns 200 only when PostgreSQL and Redis respond.

## Useful commands

```sh
docker compose logs -f api worker web
docker compose exec redis redis-cli ping
docker compose down
```

`docker compose down -v` also deletes the local PostgreSQL data volume.

## Current scope

The local stack contains a React/Vite frontend, FastAPI API, Celery worker, PostgreSQL 16 with pgvector, and Redis 7. Phase 2 provides email/password signup and login, bcrypt password hashing, 15-minute access tokens, rotating 7-day refresh sessions, CSRF-protected refresh/logout, learner/admin API authorization, a protected signed-in view, an initial Alembic schema, and idempotent starter curriculum data. The schema also reserves tables for later mentor, ingestion, code review, learning-event, and evaluation phases; those product workflows are not implemented yet.

The Compose defaults are for local development only. Production use still needs deployment-specific secret management, HTTPS and secure cookie configuration, rate limiting, CORS allowlisting, observability, backup/restore, CI/CD, security review, and operational validation described in `docs/project-plan.md`.

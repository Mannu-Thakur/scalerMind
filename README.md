# ScalerMind

ScalerMind is an AI-assisted learning platform for computer science students. The repository currently contains its architecture and requirements plus the Phase 1 local development foundation.

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

The API exposes `GET /health` as a liveness check and `GET /ready` as a dependency readiness check. `/ready` returns 200 only when PostgreSQL and Redis respond.

## Useful commands

```sh
docker compose logs -f api worker web
docker compose exec redis redis-cli ping
docker compose down
```

`docker compose down -v` also deletes the local PostgreSQL data volume.

## Current scope

The local stack contains a React/Vite frontend, FastAPI API, Celery worker, PostgreSQL 16 with pgvector installed, and Redis 7. The worker and API share the same Python image and code package. Authentication, application schema, mentor chat, document ingestion, code review, analytics, personalization, production deployment, and CI are planned for later phases and are not implemented yet.

Do not reuse the sample `.env.example` credentials in a deployed environment. Production deployment still needs the security, isolation, observability, backup, CI/CD, and operational work in `docs/project-plan.md`.

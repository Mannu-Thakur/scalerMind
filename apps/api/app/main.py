import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import settings
from app.db.engine import engine
from app.auth.router import router as auth_router

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(title="ScalerMind API", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Report that the API process is serving requests."""
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
async def ready() -> JSONResponse:
    """Report whether the API can reach its required data services."""

    async def postgres_is_ready() -> bool:
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def redis_is_ready() -> bool:
        try:
            return bool(await redis_client.ping())
        except Exception:
            return False

    postgres_ready, redis_ready = await asyncio.gather(
        postgres_is_ready(), redis_is_ready()
    )
    checks = {
        "postgres": "ok" if postgres_ready else "unavailable",
        "redis": "ok" if redis_ready else "unavailable",
    }
    is_ready = postgres_ready and redis_ready
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={"status": "ready" if is_ready else "not_ready", "checks": checks},
    )

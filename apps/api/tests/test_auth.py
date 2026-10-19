import asyncio
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.tokens import create_access_token, decode_token
from app.core.config import Settings
from app.db.base import Base
from app.db.engine import get_db
from app.db.models import RefreshSession, User
from app.main import app


@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as directory:
        database_path = Path(directory) / "auth-tests.sqlite"
        test_engine = create_async_engine(
            f"sqlite+aiosqlite:///{database_path}",
            poolclass=NullPool,
            connect_args={"timeout": 3},
        )
        initialized = False

        @event.listens_for(test_engine.sync_engine, "connect")
        def enable_sqlite_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        factory = async_sessionmaker(test_engine, expire_on_commit=False)

        async def override_get_db():
            nonlocal initialized
            if not initialized:
                async with test_engine.begin() as connection:
                    await connection.run_sync(
                        lambda sync_connection: Base.metadata.create_all(
                            sync_connection,
                            tables=[User.__table__, RefreshSession.__table__],
                        )
                    )
                initialized = True
            async with factory() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db
        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.clear()
            asyncio.run(test_engine.dispose())


def sign_up(client: TestClient, email="learner@example.com"):
    return client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "display_name": "Test Learner",
            "password": "Correct horse battery staple!",
        },
    )


def csrf_headers(client: TestClient):
    return {"X-CSRF-Token": client.cookies.get("scalermind_csrf", "")}


def test_signup_returns_learner_and_sets_http_only_refresh_cookie(client):
    response = sign_up(client)

    assert response.status_code == 201
    assert response.json()["user"]["role"] == "learner"
    assert response.json()["user"]["email"] == "learner@example.com"
    assert response.json()["access_token"]
    assert response.headers["cache-control"] == "no-store"
    assert client.cookies.get("scalermind_refresh")
    refresh_cookie = next(cookie for cookie in response.cookies.jar if cookie.name == "scalermind_refresh")
    assert refresh_cookie.has_nonstandard_attr("HttpOnly")
    expires_in = decode_token(refresh_cookie.value, "refresh").expires_at - datetime.now(timezone.utc)
    assert timedelta(days=6, hours=23) < expires_in <= timedelta(days=7)


def test_signup_cannot_escalate_role_and_duplicate_email_is_rejected(client):
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "learner@example.com",
            "display_name": "Test Learner",
            "password": "Correct horse battery staple!",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "learner"

    duplicate = sign_up(client)
    assert duplicate.status_code == 409


def test_password_policy_and_login_errors(client):
    too_short = client.post(
        "/api/auth/signup",
        json={"email": "short@example.com", "display_name": "Short", "password": "short"},
    )
    assert too_short.status_code == 422

    assert sign_up(client).status_code == 201
    valid = client.post(
        "/api/auth/login",
        json={"email": "LEARNER@example.com", "password": "Correct horse battery staple!"},
    )
    assert valid.status_code == 200
    invalid = client.post(
        "/api/auth/login",
        json={"email": "learner@example.com", "password": "wrong password"},
    )
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Invalid email or password"


def test_protected_routes_require_auth_and_enforce_roles(client):
    assert client.get("/api/users/me").status_code == 401
    assert client.get("/api/admin/me").status_code == 401

    response = sign_up(client)
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    current_user = client.get("/api/users/me", headers=headers)
    assert current_user.status_code == 200
    assert current_user.json()["email"] == "learner@example.com"
    assert client.get("/api/admin/me", headers=headers).status_code == 403


def test_refresh_rotates_token_and_reuse_revokes_the_family(client):
    assert sign_up(client).status_code == 201
    original_refresh = client.cookies.get("scalermind_refresh")
    original_csrf = client.cookies.get("scalermind_csrf")

    rotated = client.post("/api/auth/refresh", headers=csrf_headers(client))
    assert rotated.status_code == 200
    new_refresh = client.cookies.get("scalermind_refresh")
    new_csrf = client.cookies.get("scalermind_csrf")
    assert new_refresh and new_refresh != original_refresh

    client.cookies.set("scalermind_refresh", original_refresh, path="/api/auth")
    replay = client.post("/api/auth/refresh", headers={"X-CSRF-Token": new_csrf})
    assert replay.status_code == 401

    client.cookies.set("scalermind_refresh", new_refresh, path="/api/auth")
    client.cookies.set("scalermind_csrf", new_csrf, path="/")
    after_replay = client.post("/api/auth/refresh", headers={"X-CSRF-Token": new_csrf})
    assert after_replay.status_code == 401
    assert "reuse" in after_replay.json()["detail"]
    assert original_csrf


def test_refresh_requires_csrf_and_logout_revokes_refresh_session(client):
    assert client.post("/api/auth/refresh").status_code == 401
    assert sign_up(client).status_code == 201
    csrf = client.cookies.get("scalermind_csrf")
    refresh = client.cookies.get("scalermind_refresh")

    assert client.post("/api/auth/refresh").status_code == 403
    logout = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    assert logout.status_code == 204

    client.cookies.set("scalermind_refresh", refresh, path="/api/auth")
    client.cookies.set("scalermind_csrf", csrf, path="/")
    assert client.post("/api/auth/refresh", headers={"X-CSRF-Token": csrf}).status_code == 401


def test_access_token_must_be_the_expected_token_type():
    token = create_access_token(uuid4())
    with pytest.raises(ValueError, match="Invalid or expired token"):
        decode_token(token, "refresh")
    assert decode_token(token, "access").token_type == "access"


def test_production_requires_a_stable_secret_and_secure_cookies():
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(app_env="production")
    with pytest.raises(ValidationError, match="SECURE_AUTH_COOKIES"):
        Settings(app_env="production", jwt_secret_key="s" * 32)

    configured = Settings(
        app_env="production",
        jwt_secret_key="s" * 32,
        secure_auth_cookies=True,
    )
    assert configured.signing_key == "s" * 32

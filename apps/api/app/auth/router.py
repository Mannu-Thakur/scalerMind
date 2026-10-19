import hmac
import secrets
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.auth.passwords import hash_password, verify_password, verify_unknown_user_password
from app.auth.schemas import LoginRequest, SignUpRequest, TokenResponse, UserRead
from app.auth.tokens import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
)
from app.core.config import settings
from app.db.engine import get_db
from app.db.models import RefreshSession, User

router = APIRouter(tags=["authentication"])


def _csrf_value() -> str:
    return secrets.token_urlsafe(32)


def _set_session_cookies(response: Response, refresh_token: str, csrf_token: str) -> None:
    common = {
        "secure": settings.secure_auth_cookies,
        "samesite": "strict",
        "max_age": settings.refresh_token_days * 24 * 60 * 60,
    }
    response.set_cookie(
        settings.refresh_cookie_name,
        refresh_token,
        httponly=True,
        path="/api/auth",
        **common,
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        httponly=False,
        path="/",
        **common,
    )


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(
        settings.refresh_cookie_name,
        path="/api/auth",
        secure=settings.secure_auth_cookies,
        httponly=True,
        samesite="strict",
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        path="/",
        secure=settings.secure_auth_cookies,
        httponly=False,
        samesite="strict",
    )


def _require_csrf(request: Request) -> None:
    cookie = request.cookies.get(settings.csrf_cookie_name, "")
    header = request.headers.get("x-csrf-token", "")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


async def _issue_session(
    *, session: AsyncSession, user: User, response: Response, family_id: UUID | None = None
) -> TokenResponse:
    family_id = family_id or uuid4()
    encoded_refresh, jti, expires_at = create_refresh_token(user.id, family_id)
    session.add(
        RefreshSession(
            user_id=user.id,
            family_id=family_id,
            jti=jti,
            token_hash=hash_refresh_token(encoded_refresh),
            expires_at=expires_at,
        )
    )
    await session.commit()
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    _set_session_cookies(response, encoded_refresh, _csrf_value())
    return TokenResponse(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")


def _as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes for timezone-aware columns in tests."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


@router.post("/api/auth/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    payload: SignUpRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = User(
        email=str(payload.email).lower(),
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        role="learner",
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered") from None
    await session.refresh(user)
    return await _issue_session(session=session, user=user, response=response)


@router.post("/api/auth/login", response_model=TokenResponse)
async def log_in(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None:
        verify_unknown_user_password(payload.password)
        raise _unauthorized()
    if not user.is_active or not verify_password(payload.password, user.password_hash):
        raise _unauthorized()
    return await _issue_session(session=session, user=user, response=response)


@router.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_session(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    encoded_refresh = request.cookies.get(settings.refresh_cookie_name)
    if not encoded_refresh:
        _clear_session_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is missing")
    _require_csrf(request)
    try:
        claims = decode_token(encoded_refresh, "refresh")
    except ValueError:
        _clear_session_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is invalid") from None
    if claims.family_id is None:
        _clear_session_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is invalid")

    current = await session.scalar(
        select(RefreshSession).where(RefreshSession.jti == claims.token_id).with_for_update()
    )
    if current is None or current.token_hash != hash_refresh_token(encoded_refresh):
        _clear_session_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is invalid")
    if current.revoked_at is not None:
        await session.execute(
            update(RefreshSession)
            .where(RefreshSession.family_id == current.family_id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await session.commit()
        _clear_session_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token reuse detected")
    if current.user_id != claims.user_id or current.family_id != claims.family_id:
        _clear_session_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is invalid")

    user = await session.scalar(select(User).where(User.id == current.user_id))
    if user is None or not user.is_active:
        current.revoked_at = datetime.now(timezone.utc)
        await session.commit()
        _clear_session_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is invalid")

    now = datetime.now(timezone.utc)
    if _as_utc(current.expires_at) <= now:
        current.revoked_at = now
        await session.commit()
        _clear_session_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session has expired")

    next_refresh, next_jti, expires_at = create_refresh_token(user.id, current.family_id)
    current.revoked_at = now
    current.replaced_by_jti = next_jti
    session.add(
        RefreshSession(
            user_id=user.id,
            family_id=current.family_id,
            jti=next_jti,
            token_hash=hash_refresh_token(next_refresh),
            expires_at=expires_at,
        )
    )
    await session.commit()
    _set_session_cookies(response, next_refresh, _csrf_value())
    return TokenResponse(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


@router.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def log_out(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> Response:
    _require_csrf(request)
    encoded_refresh = request.cookies.get(settings.refresh_cookie_name)
    if encoded_refresh:
        try:
            claims = decode_token(encoded_refresh, "refresh")
            current = await session.scalar(
                select(RefreshSession).where(RefreshSession.jti == claims.token_id).with_for_update()
            )
            if current and current.token_hash == hash_refresh_token(encoded_refresh) and current.revoked_at is None:
                current.revoked_at = datetime.now(timezone.utc)
                await session.commit()
        except ValueError:
            await session.rollback()
    _clear_session_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/api/users/me", response_model=UserRead)
async def read_current_user(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.get("/api/admin/me", response_model=UserRead)
async def read_admin_user(user: User = Depends(require_admin)) -> UserRead:
    return UserRead.model_validate(user)

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Literal
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings

JWT_ISSUER = "scalermind"
JWT_AUDIENCE = "scalermind-api"
JWT_ALGORITHM = "HS256"
TokenType = Literal["access", "refresh"]


@dataclass(frozen=True)
class DecodedToken:
    user_id: UUID
    token_id: UUID
    token_type: TokenType
    family_id: UUID | None
    expires_at: datetime


def _encode(
    *, user_id: UUID, token_id: UUID, token_type: TokenType, lifetime: timedelta,
    family_id: UUID | None = None,
) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + lifetime
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "jti": str(token_id),
        "typ": token_type,
        "iat": now,
        "exp": expires_at,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
    }
    if family_id is not None:
        payload["fid"] = str(family_id)
    return jwt.encode(payload, settings.signing_key, algorithm=JWT_ALGORITHM), expires_at


def create_access_token(user_id: UUID) -> str:
    encoded, _ = _encode(
        user_id=user_id,
        token_id=uuid4(),
        token_type="access",
        lifetime=timedelta(minutes=settings.access_token_minutes),
    )
    return encoded


def create_refresh_token(
    user_id: UUID, family_id: UUID, token_id: UUID | None = None
) -> tuple[str, UUID, datetime]:
    token_id = token_id or uuid4()
    encoded, expires_at = _encode(
        user_id=user_id,
        token_id=token_id,
        token_type="refresh",
        lifetime=timedelta(days=settings.refresh_token_days),
        family_id=family_id,
    )
    return encoded, token_id, expires_at


def decode_token(encoded: str, expected_type: TokenType) -> DecodedToken:
    try:
        payload = jwt.decode(
            encoded,
            settings.signing_key,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": ["sub", "jti", "typ", "iat", "exp", "iss", "aud"]},
        )
        if payload.get("typ") != expected_type:
            raise InvalidTokenError("Wrong token type")
        family_id = UUID(payload["fid"]) if payload.get("fid") else None
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        return DecodedToken(
            user_id=UUID(payload["sub"]),
            token_id=UUID(payload["jti"]),
            token_type=expected_type,
            family_id=family_id,
            expires_at=expires_at,
        )
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid or expired token") from exc


def hash_refresh_token(encoded: str) -> str:
    return sha256(encoded.encode("utf-8")).hexdigest()

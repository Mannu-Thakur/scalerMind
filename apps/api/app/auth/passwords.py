import secrets

import bcrypt

PASSWORD_MIN_CHARACTERS = 12
PASSWORD_MAX_BYTES = 72
BCRYPT_COST = 12

_DUMMY_PASSWORD_HASH = bcrypt.hashpw(
    secrets.token_urlsafe(32).encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_COST)
)


def validate_password(password: str) -> str | None:
    encoded = password.encode("utf-8")
    if len(password) < PASSWORD_MIN_CHARACTERS:
        return f"Password must be at least {PASSWORD_MIN_CHARACTERS} characters long"
    if len(encoded) > PASSWORD_MAX_BYTES:
        return f"Password must be at most {PASSWORD_MAX_BYTES} UTF-8 bytes"
    return None


def hash_password(password: str) -> str:
    validation_error = validate_password(password)
    if validation_error:
        raise ValueError(validation_error)
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_COST)
    ).decode("ascii")


def verify_password(password: str, encoded_hash: str) -> bool:
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), encoded_hash.encode("ascii"))
    except (ValueError, TypeError, UnicodeEncodeError):
        return False


def verify_unknown_user_password(password: str) -> None:
    """Spend a bcrypt verification for unknown emails to reduce timing leaks."""
    if len(password.encode("utf-8")) <= PASSWORD_MAX_BYTES:
        bcrypt.checkpw(password.encode("utf-8"), _DUMMY_PASSWORD_HASH)

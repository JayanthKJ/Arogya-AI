from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(subject: str, extra_claims: Optional[dict] = None) -> str:
    """
    Create a signed JWT.

    :param subject: value stored in the ``sub`` claim (user id).
    :param extra_claims: any additional payload fields.
    :return: encoded JWT string.
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iss": "arogya-ai"
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    :raises JWTError: if token is invalid or expired.
    :return: decoded payload dict.
    """
    settings = get_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

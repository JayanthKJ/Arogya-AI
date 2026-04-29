from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import Session, select

from auth.utils import decode_access_token
from config.database import get_session
from models.db_models import User

_bearer = HTTPBearer(auto_error=True)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_session),
) -> User:
    """
    FastAPI dependency that extracts the JWT from the Authorization header,
    validates it, and returns the corresponding User row.

    Raises HTTP 401 for any invalid / expired token or unknown user.
    """
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if not isinstance(user_id, str):
            raise _CREDENTIALS_EXCEPTION
    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    try:
        user = db.exec(select(User).where(User.id == user_id)).first()
    except Exception:
        raise _CREDENTIALS_EXCEPTION
    if user is None:
        raise _CREDENTIALS_EXCEPTION

    return user

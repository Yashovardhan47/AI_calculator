from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings
from ..storage import get_store
from .security import TokenError, decode_token


bearer = HTTPBearer(auto_error=False)


def _resolve_user(credentials: HTTPAuthorizationCredentials | None) -> dict | None:
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_token(
            credentials.credentials,
            secret=settings.jwt_secret,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expected_type="access",
        )
    except TokenError:
        return None
    return get_store().get_user_by_id(payload["sub"])


def optional_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict | None:
    return _resolve_user(credentials)


def current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict:
    user = _resolve_user(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Authentication is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

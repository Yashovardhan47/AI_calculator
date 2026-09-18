from __future__ import annotations

import hmac
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool

from ..config import settings
from ..storage import StoreConflict, get_store
from .dependencies import current_user
from .google_identity import verify_google_id_token
from .schemas import AuthResponse, GoogleAuthRequest, LoginRequest, ProfileUpdateRequest, RegisterRequest, UserResponse
from .security import (
    TokenError,
    create_token,
    decode_token,
    hash_password,
    token_hash,
    utc_from_timestamp,
    verify_password,
)


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
REFRESH_COOKIE = "omnicalc_refresh"


def _public_user(user: dict) -> dict:
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "display_name": user.get("display_name"),
        "auth_provider": user.get("auth_provider", "local"),
        "email_verified": bool(user.get("email_verified")),
        "avatar_url": user.get("avatar_url"),
        "created_at": user.get("created_at"),
    }


def _set_refresh_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/api/v1/auth",
    )


def _require_trusted_origin(request: Request) -> None:
    """Reject browser credential requests originating outside the configured UI."""
    origin = request.headers.get("origin")
    if origin and origin not in settings.allowed_origins:
        raise HTTPException(status_code=403, detail={"message": "Untrusted authentication origin."})


def _issue_session(user: dict, response: Response, user_agent: str | None) -> dict:
    store = get_store()
    session_id = str(uuid4())
    access_lifetime = timedelta(minutes=settings.access_token_minutes)
    refresh_lifetime = timedelta(days=settings.refresh_token_days)
    access_token, _ = create_token(
        subject=str(user["id"]),
        token_type="access",
        secret=settings.jwt_secret,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        lifetime=access_lifetime,
        session_id=session_id,
    )
    refresh_token, refresh_claims = create_token(
        subject=str(user["id"]),
        token_type="refresh",
        secret=settings.jwt_secret,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        lifetime=refresh_lifetime,
        session_id=session_id,
    )
    store.save_refresh_session(
        session_id=session_id,
        user_id=str(user["id"]),
        refresh_hash=token_hash(refresh_token),
        expires_at=utc_from_timestamp(refresh_claims["exp"]),
        user_agent=user_agent,
    )
    _set_refresh_cookie(response, refresh_token, int(refresh_lifetime.total_seconds()))
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_lifetime.total_seconds()),
        "user": _public_user(user),
    }


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, response: Response) -> dict:
    _require_trusted_origin(request)
    try:
        user = get_store().create_local_user(payload.email, payload.display_name.strip(), hash_password(payload.password))
    except StoreConflict as exc:
        raise HTTPException(status_code=409, detail={"message": str(exc)}) from exc
    return _issue_session(user, response, request.headers.get("user-agent"))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response) -> dict:
    _require_trusted_origin(request)
    store = get_store()
    user = store.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user.get("password_hash")):
        raise HTTPException(status_code=401, detail={"message": "Invalid email or password."})
    store.update_last_login(str(user["id"]))
    return _issue_session(user, response, request.headers.get("user-agent"))


@router.post("/google", response_model=AuthResponse)
async def google_login(payload: GoogleAuthRequest, request: Request, response: Response) -> dict:
    _require_trusted_origin(request)
    try:
        identity = await run_in_threadpool(verify_google_id_token, payload.credential, settings.google_client_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"message": "Google identity verification failed."}) from exc

    store = get_store()
    user = store.get_user_by_google_sub(identity["sub"])
    if user is None:
        existing = store.get_user_by_email(identity["email"])
        if existing:
            raise HTTPException(
                status_code=409,
                detail={"message": "This email already has an OmniCalc account. Sign in using its original method."},
            )
        try:
            user = store.create_google_user(
                email=identity["email"].lower(),
                display_name=identity.get("name") or identity["email"].split("@", 1)[0],
                google_sub=identity["sub"],
                avatar_url=identity.get("picture"),
            )
        except StoreConflict as exc:
            raise HTTPException(status_code=409, detail={"message": str(exc)}) from exc
    store.update_last_login(str(user["id"]))
    return _issue_session(user, response, request.headers.get("user-agent"))


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response) -> dict:
    _require_trusted_origin(request)
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise HTTPException(status_code=401, detail={"message": "Refresh session is missing."})
    try:
        claims = decode_token(
            refresh_token,
            secret=settings.jwt_secret,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expected_type="refresh",
        )
    except TokenError as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail={"message": "Refresh session is invalid or expired."}) from exc

    store = get_store()
    session = store.get_refresh_session(claims["sid"])
    session_expired = session and session["expires_at"] <= datetime.now(timezone.utc)
    valid_hash = session and hmac.compare_digest(session["token_hash"], token_hash(refresh_token))
    if not session or session.get("revoked_at") or session_expired or not valid_hash:
        if session:
            store.revoke_all_sessions(claims["sub"])
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail={"message": "Refresh session has been revoked."})
    user = store.get_user_by_id(claims["sub"])
    if not user:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail={"message": "User account is unavailable."})
    store.revoke_refresh_session(claims["sid"])
    return _issue_session(user, response, request.headers.get("user-agent"))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response) -> None:
    _require_trusted_origin(request)
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if refresh_token:
        try:
            claims = decode_token(
                refresh_token,
                secret=settings.jwt_secret,
                issuer=settings.jwt_issuer,
                audience=settings.jwt_audience,
                expected_type="refresh",
            )
            get_store().revoke_refresh_session(claims["sid"])
        except TokenError:
            pass
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[dict, Depends(current_user)]) -> dict:
    return _public_user(user)


@router.patch("/me", response_model=UserResponse)
def update_me(payload: ProfileUpdateRequest, user: Annotated[dict, Depends(current_user)]) -> dict:
    updated = get_store().update_profile(str(user["id"]), payload.display_name.strip())
    return _public_user(updated)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(response: Response, user: Annotated[dict, Depends(current_user)]) -> None:
    store = get_store()
    store.revoke_all_sessions(str(user["id"]))
    store.delete_user(str(user["id"]))
    _clear_refresh_cookie(response)

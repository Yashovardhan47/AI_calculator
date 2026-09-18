from __future__ import annotations

from typing import Any


def verify_google_id_token(credential: str, client_id: str) -> dict[str, Any]:
    if not client_id:
        raise RuntimeError("Google authentication is not configured.")
    from google.auth.transport import requests
    from google.oauth2 import id_token

    payload = id_token.verify_oauth2_token(credential, requests.Request(), client_id)
    if payload.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise ValueError("Invalid Google token issuer.")
    if payload.get("aud") != client_id:
        raise ValueError("Invalid Google token audience.")
    if not payload.get("sub") or not payload.get("email") or payload.get("email_verified") is not True:
        raise ValueError("Google account email is not verified.")
    return payload

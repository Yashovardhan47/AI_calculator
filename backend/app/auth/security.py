from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


class TokenError(ValueError):
    pass


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    n, r, p = 2**14, 8, 1
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=32)
    return f"scrypt${n}${r}${p}${_b64encode(salt)}${_b64encode(derived)}"


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$", 5)
        if algorithm != "scrypt":
            return False
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_b64decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=32,
        )
        return hmac.compare_digest(derived, _b64decode(expected))
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_token(
    *,
    subject: str,
    token_type: str,
    secret: str,
    issuer: str,
    audience: str,
    lifetime: timedelta,
    session_id: str,
) -> tuple[str, dict[str, Any]]:
    now = int(time.time())
    payload = {
        "sub": subject,
        "type": token_type,
        "sid": session_id,
        "jti": str(uuid4()),
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "nbf": now,
        "exp": now + int(lifetime.total_seconds()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64encode(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}", payload


def decode_token(
    token: str,
    *,
    secret: str,
    issuer: str,
    audience: str,
    expected_type: str,
) -> dict[str, Any]:
    if len(token) > 4096:
        raise TokenError("Token is too large.")
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        header = json.loads(_b64decode(encoded_header))
        payload = json.loads(_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TokenError("Malformed token.") from exc
    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise TokenError("Unsupported token algorithm.")
    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    try:
        supplied_signature = _b64decode(encoded_signature)
    except ValueError as exc:
        raise TokenError("Malformed signature.") from exc
    if not hmac.compare_digest(expected_signature, supplied_signature):
        raise TokenError("Invalid token signature.")
    now = int(time.time())
    if payload.get("iss") != issuer or payload.get("aud") != audience:
        raise TokenError("Invalid token issuer or audience.")
    if payload.get("type") != expected_type:
        raise TokenError("Invalid token type.")
    if not isinstance(payload.get("exp"), int) or payload["exp"] <= now:
        raise TokenError("Token has expired.")
    if not isinstance(payload.get("nbf"), int) or payload["nbf"] > now + 30:
        raise TokenError("Token is not active.")
    if not payload.get("sub") or not payload.get("sid"):
        raise TokenError("Token is missing required claims.")
    return payload


def utc_from_timestamp(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

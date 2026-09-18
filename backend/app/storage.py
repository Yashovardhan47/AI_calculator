from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import settings


class StoreConflict(ValueError):
    pass


class StoreNotFound(ValueError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryStore:
    """Thread-safe development/test store used only when DATABASE_URL is empty."""

    mode = "memory"

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.users: dict[str, dict[str, Any]] = {}
        self.refresh_sessions: dict[str, dict[str, Any]] = {}
        self.history: dict[str, list[dict[str, Any]]] = {}
        self.workflows: dict[str, list[dict[str, Any]]] = {}

    def create_local_user(self, email: str, display_name: str, password_hash: str) -> dict[str, Any]:
        with self._lock:
            if self.get_user_by_email(email):
                raise StoreConflict("An account already exists for this email.")
            user = {
                "id": str(uuid4()),
                "email": email,
                "display_name": display_name,
                "password_hash": password_hash,
                "auth_provider": "local",
                "google_sub": None,
                "email_verified": False,
                "avatar_url": None,
                "status": "active",
                "created_at": _now(),
                "updated_at": _now(),
                "last_login_at": None,
            }
            self.users[user["id"]] = user
            return dict(user)

    def create_google_user(self, *, email: str, display_name: str, google_sub: str, avatar_url: str | None) -> dict[str, Any]:
        with self._lock:
            if self.get_user_by_google_sub(google_sub):
                raise StoreConflict("This Google account is already linked.")
            if self.get_user_by_email(email):
                raise StoreConflict("An account already exists for this email. Sign in with its original method first.")
            user = {
                "id": str(uuid4()),
                "email": email,
                "display_name": display_name,
                "password_hash": None,
                "auth_provider": "google",
                "google_sub": google_sub,
                "email_verified": True,
                "avatar_url": avatar_url,
                "status": "active",
                "created_at": _now(),
                "updated_at": _now(),
                "last_login_at": _now(),
            }
            self.users[user["id"]] = user
            return dict(user)

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        user = self.users.get(str(user_id))
        return dict(user) if user else None

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        normalized = email.lower()
        user = next((item for item in self.users.values() if item["email"].lower() == normalized), None)
        return dict(user) if user else None

    def get_user_by_google_sub(self, google_sub: str) -> dict[str, Any] | None:
        user = next((item for item in self.users.values() if item.get("google_sub") == google_sub), None)
        return dict(user) if user else None

    def update_last_login(self, user_id: str) -> None:
        with self._lock:
            self.users[str(user_id)]["last_login_at"] = _now()

    def update_profile(self, user_id: str, display_name: str) -> dict[str, Any]:
        with self._lock:
            user = self.users.get(str(user_id))
            if not user:
                raise StoreNotFound("User not found.")
            user["display_name"] = display_name
            user["updated_at"] = _now()
            return dict(user)

    def save_refresh_session(
        self,
        *,
        session_id: str,
        user_id: str,
        refresh_hash: str,
        expires_at: datetime,
        user_agent: str | None,
    ) -> None:
        with self._lock:
            self.refresh_sessions[session_id] = {
                "id": session_id,
                "user_id": str(user_id),
                "token_hash": refresh_hash,
                "expires_at": expires_at,
                "revoked_at": None,
                "user_agent": user_agent,
                "created_at": _now(),
            }

    def get_refresh_session(self, session_id: str) -> dict[str, Any] | None:
        session = self.refresh_sessions.get(session_id)
        return dict(session) if session else None

    def revoke_refresh_session(self, session_id: str) -> None:
        with self._lock:
            session = self.refresh_sessions.get(session_id)
            if session:
                session["revoked_at"] = _now()

    def revoke_all_sessions(self, user_id: str) -> None:
        with self._lock:
            for session in self.refresh_sessions.values():
                if session["user_id"] == str(user_id):
                    session["revoked_at"] = _now()

    def save_calculation(self, user_id: str, result: dict[str, Any]) -> str:
        item = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "query": result["query"],
            "calculator": result["calculator"],
            "result": result,
            "created_at": _now(),
        }
        with self._lock:
            self.history.setdefault(str(user_id), []).insert(0, item)
        return item["id"]

    def list_history(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return [dict(item) for item in self.history.get(str(user_id), [])[:limit]]

    def delete_history_item(self, user_id: str, history_id: str) -> bool:
        with self._lock:
            items = self.history.get(str(user_id), [])
            remaining = [item for item in items if item["id"] != history_id]
            self.history[str(user_id)] = remaining
            return len(remaining) != len(items)

    def clear_history(self, user_id: str) -> None:
        with self._lock:
            self.history[str(user_id)] = []

    def save_workflow(self, user_id: str, name: str, description: str | None, definition: dict[str, Any]) -> dict[str, Any]:
        item = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "name": name,
            "description": description,
            "workflow_definition": definition,
            "version": 1,
            "created_at": _now(),
            "updated_at": _now(),
        }
        with self._lock:
            self.workflows.setdefault(str(user_id), []).insert(0, item)
        return dict(item)

    def list_workflows(self, user_id: str) -> list[dict[str, Any]]:
        return [dict(item) for item in self.workflows.get(str(user_id), [])]

    def delete_workflow(self, user_id: str, workflow_id: str) -> bool:
        with self._lock:
            items = self.workflows.get(str(user_id), [])
            remaining = [item for item in items if item["id"] != workflow_id]
            self.workflows[str(user_id)] = remaining
            return len(remaining) != len(items)

    def delete_user(self, user_id: str) -> bool:
        with self._lock:
            existed = self.users.pop(str(user_id), None) is not None
            self.history.pop(str(user_id), None)
            self.workflows.pop(str(user_id), None)
            self.revoke_all_sessions(str(user_id))
            return existed


class PostgresStore:
    mode = "postgresql"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self.database_url, row_factory=dict_row)

    @staticmethod
    def _row(row) -> dict[str, Any] | None:
        if not row:
            return None
        payload = dict(row)
        if "id" in payload:
            payload["id"] = str(payload["id"])
        if "user_id" in payload:
            payload["user_id"] = str(payload["user_id"])
        return payload

    def create_local_user(self, email: str, display_name: str, password_hash: str) -> dict[str, Any]:
        import psycopg

        try:
            with self._connect() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO users (email, display_name, password_hash, auth_provider, email_verified)
                       VALUES (%s, %s, %s, 'local', FALSE) RETURNING *""",
                    (email, display_name, password_hash),
                )
                return self._row(cursor.fetchone())
        except psycopg.errors.UniqueViolation as exc:
            raise StoreConflict("An account already exists for this email.") from exc

    def create_google_user(self, *, email: str, display_name: str, google_sub: str, avatar_url: str | None) -> dict[str, Any]:
        import psycopg

        try:
            with self._connect() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO users
                       (email, display_name, auth_provider, google_sub, email_verified, avatar_url, last_login_at)
                       VALUES (%s, %s, 'google', %s, TRUE, %s, NOW()) RETURNING *""",
                    (email, display_name, google_sub, avatar_url),
                )
                return self._row(cursor.fetchone())
        except psycopg.errors.UniqueViolation as exc:
            raise StoreConflict("An account already exists for this email or Google identity.") from exc

    def _one(self, query: str, params: tuple) -> dict[str, Any] | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(query, params)
            return self._row(cursor.fetchone())

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM users WHERE id = %s AND status = 'active'", (user_id,))

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM users WHERE LOWER(email) = LOWER(%s) AND status = 'active'", (email,))

    def get_user_by_google_sub(self, google_sub: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM users WHERE google_sub = %s AND status = 'active'", (google_sub,))

    def update_last_login(self, user_id: str) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user_id,))

    def update_profile(self, user_id: str, display_name: str) -> dict[str, Any]:
        user = self._one(
            "UPDATE users SET display_name = %s, updated_at = NOW() WHERE id = %s RETURNING *",
            (display_name, user_id),
        )
        if not user:
            raise StoreNotFound("User not found.")
        return user

    def save_refresh_session(self, *, session_id: str, user_id: str, refresh_hash: str, expires_at: datetime, user_agent: str | None) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, user_agent)
                   VALUES (%s, %s, %s, %s, %s)""",
                (session_id, user_id, refresh_hash, expires_at, user_agent),
            )

    def get_refresh_session(self, session_id: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM refresh_tokens WHERE id = %s", (session_id,))

    def revoke_refresh_session(self, session_id: str) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = %s AND revoked_at IS NULL", (session_id,))

    def revoke_all_sessions(self, user_id: str) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE refresh_tokens SET revoked_at = NOW() WHERE user_id = %s AND revoked_at IS NULL", (user_id,))

    def save_calculation(self, user_id: str, result: dict[str, Any]) -> str:
        from psycopg.types.json import Jsonb

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO calculation_history
                   (user_id, original_query, normalized_query, calculator_id, result, routing_source)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (
                    user_id,
                    result["query"],
                    result["query"],
                    result["calculator"],
                    Jsonb(result),
                    result.get("metadata", {}).get("routing_source", "local"),
                ),
            )
            return str(cursor.fetchone()["id"])

    def list_history(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, user_id, original_query AS query, calculator_id AS calculator, result, created_at
                   FROM calculation_history WHERE user_id = %s ORDER BY created_at DESC LIMIT %s""",
                (user_id, limit),
            )
            return [self._row(row) for row in cursor.fetchall()]

    def delete_history_item(self, user_id: str, history_id: str) -> bool:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM calculation_history WHERE id = %s AND user_id = %s", (history_id, user_id))
            return cursor.rowcount > 0

    def clear_history(self, user_id: str) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM calculation_history WHERE user_id = %s", (user_id,))

    def save_workflow(self, user_id: str, name: str, description: str | None, definition: dict[str, Any]) -> dict[str, Any]:
        from psycopg.types.json import Jsonb

        return self._one(
            """INSERT INTO saved_workflows (user_id, name, description, workflow_definition)
               VALUES (%s, %s, %s, %s) RETURNING *""",
            (user_id, name, description, Jsonb(definition)),
        )

    def list_workflows(self, user_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM saved_workflows WHERE user_id = %s ORDER BY updated_at DESC", (user_id,))
            return [self._row(row) for row in cursor.fetchall()]

    def delete_workflow(self, user_id: str, workflow_id: str) -> bool:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM saved_workflows WHERE id = %s AND user_id = %s", (workflow_id, user_id))
            return cursor.rowcount > 0

    def delete_user(self, user_id: str) -> bool:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            return cursor.rowcount > 0


_store: MemoryStore | PostgresStore | None = None


def get_store() -> MemoryStore | PostgresStore:
    global _store
    if _store is None:
        _store = PostgresStore(settings.database_url) if settings.database_url else MemoryStore()
    return _store


def set_store(store: MemoryStore | PostgresStore | None) -> None:
    global _store
    _store = store

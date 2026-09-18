import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.auth.security import create_token
from app.config import settings
from app.storage import MemoryStore, set_store

from datetime import timedelta


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        set_store(MemoryStore())
        self.client = TestClient(app)

    def tearDown(self):
        set_store(None)

    def register(self, email="yash@example.com"):
        return self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "StrongPass123", "display_name": "Yash"},
        )

    def test_register_returns_access_token_and_http_only_refresh_cookie(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["email"], "yash@example.com")
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertIn("omnicalc_refresh", response.cookies)
        self.assertIn("HttpOnly", response.headers["set-cookie"])

    def test_access_token_protects_profile(self):
        registered = self.register().json()
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {registered['access_token']}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["display_name"], "Yash")

    def test_tampered_and_wrong_type_tokens_are_rejected(self):
        registered = self.register().json()
        token = registered["access_token"]
        replacement = "a" if token[-1] != "a" else "b"
        tampered = f"{token[:-1]}{replacement}"
        self.assertEqual(
            self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"}).status_code,
            401,
        )
        refresh_token, _ = create_token(
            subject=registered["user"]["id"],
            token_type="refresh",
            secret=settings.jwt_secret,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            lifetime=timedelta(days=1),
            session_id="not-an-access-session",
        )
        self.assertEqual(
            self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh_token}"}).status_code,
            401,
        )

    def test_duplicate_registration_and_invalid_login_are_rejected(self):
        self.register()
        self.assertEqual(self.register().status_code, 409)
        bad_login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "yash@example.com", "password": "incorrect"},
        )
        self.assertEqual(bad_login.status_code, 401)

    def test_registration_policy_and_browser_origin_are_enforced(self):
        weak = self.client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "password": "alllowercase", "display_name": "Weak"},
        )
        self.assertEqual(weak.status_code, 422)
        untrusted = self.client.post(
            "/api/v1/auth/login",
            headers={"Origin": "https://evil.example"},
            json={"email": "nobody@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(untrusted.status_code, 403)

    def test_login_refresh_rotation_and_logout(self):
        self.register()
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "yash@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(login.status_code, 200)
        first_refresh = login.cookies["omnicalc_refresh"]
        refreshed = self.client.post("/api/v1/auth/refresh")
        self.assertEqual(refreshed.status_code, 200)
        self.assertNotEqual(first_refresh, refreshed.cookies["omnicalc_refresh"])
        logout = self.client.post("/api/v1/auth/logout")
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(self.client.post("/api/v1/auth/refresh").status_code, 401)

    @patch("app.auth.router.verify_google_id_token")
    def test_google_identity_creates_and_reuses_federated_account(self, verify_google):
        verify_google.return_value = {
            "sub": "google-stable-user-id",
            "email": "yash@gmail.com",
            "email_verified": True,
            "name": "Yash Google",
            "picture": "https://example.com/avatar.png",
            "aud": "test-client",
            "iss": "https://accounts.google.com",
        }
        first = self.client.post("/api/v1/auth/google", json={"credential": "x" * 120})
        second = self.client.post("/api/v1/auth/google", json={"credential": "y" * 120})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["user"]["id"], second.json()["user"]["id"])
        self.assertEqual(first.json()["user"]["auth_provider"], "google")

    def test_authenticated_calculation_is_saved_to_user_history(self):
        registered = self.register().json()
        headers = {"Authorization": f"Bearer {registered['access_token']}"}
        calculated = self.client.post(
            "/api/v1/calculate",
            json={"query": "Calculate 2 + 2"},
            headers=headers,
        )
        self.assertEqual(calculated.status_code, 200)
        self.assertIn("history_id", calculated.json()["metadata"])
        history = self.client.get("/api/v1/history", headers=headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()["items"]), 1)
        self.assertEqual(history.json()["items"][0]["result"]["value"], 4)

    def test_history_and_workflows_are_isolated_by_user(self):
        first = self.register("first@example.com").json()
        second = self.register("second@example.com").json()
        first_headers = {"Authorization": f"Bearer {first['access_token']}"}
        second_headers = {"Authorization": f"Bearer {second['access_token']}"}

        self.client.post("/api/v1/calculate", json={"query": "Calculate 8 * 7"}, headers=first_headers)
        first_history = self.client.get("/api/v1/history", headers=first_headers).json()["items"]
        self.assertEqual(len(first_history), 1)
        self.assertEqual(self.client.get("/api/v1/history", headers=second_headers).json()["items"], [])
        self.assertEqual(
            self.client.delete(f"/api/v1/history/{first_history[0]['id']}", headers=second_headers).status_code,
            404,
        )

        workflow = self.client.post(
            "/api/v1/workflows",
            json={"name": "Seven eights", "description": "Calculate 8 * 7", "workflow_definition": {"query": "Calculate 8 * 7"}},
            headers=first_headers,
        )
        self.assertEqual(workflow.status_code, 201)
        self.assertEqual(self.client.get("/api/v1/workflows", headers=second_headers).json()["items"], [])
        self.assertEqual(
            self.client.delete(f"/api/v1/workflows/{workflow.json()['id']}", headers=second_headers).status_code,
            404,
        )

    def test_profile_update_and_account_deletion(self):
        registered = self.register().json()
        headers = {"Authorization": f"Bearer {registered['access_token']}"}
        updated = self.client.patch("/api/v1/auth/me", json={"display_name": "Updated User"}, headers=headers)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["display_name"], "Updated User")
        self.assertEqual(self.client.delete("/api/v1/auth/me", headers=headers).status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=headers).status_code, 401)

    def test_cors_preflight_allows_workspace_mutations_from_trusted_origin(self):
        response = self.client.options(
            "/api/v1/history",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "DELETE",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("DELETE", response.headers["access-control-allow-methods"])


if __name__ == "__main__":
    unittest.main()

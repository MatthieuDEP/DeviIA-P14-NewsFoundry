"""Tests d'authentification sur SQLite, sans toucher à PostgreSQL."""

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import bcrypt
import jwt
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
with patch.dict(os.environ, {
    "DATABASE_URL": "sqlite://",
    "CORS_ORIGINS": "http://localhost:3000,http://127.0.0.1:3000",
}):
    import database
    from main import app
    from models import User

SECRET = "test-key-only-not-for-production-123456789"
LOGIN = {"email": "test@test.com", "password": "test"}


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )
        self.env_patch = patch.dict(os.environ, {"JWT_SECRET_KEY": SECRET})
        self.env_patch.start()
        self.engine_patch = patch.object(database, "engine", self.engine)
        self.engine_patch.start()
        database.init_db()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine_patch.stop()
        self.env_patch.stop()
        self.engine.dispose()

    def test_login_and_current_user(self):
        response = self.client.post("/login", json=LOGIN)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertEqual(response.headers["cache-control"], "no-store")
        token = response.json()["access_token"]
        claims = jwt.decode(token, SECRET, algorithms=["HS256"])
        self.assertEqual(claims["sub"], "1")
        self.assertEqual(claims["exp"] - claims["iat"], 3600)
        response = self.client.get("/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": 1, "email": "test@test.com"})

    def test_incorrect_credentials(self):
        for body in [{**LOGIN, "password": "wrong"}, {**LOGIN, "email": "unknown@example.com"}]:
            with self.subTest(body=body):
                response = self.client.post("/login", json=body)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json(), {"detail": "Email ou mot de passe incorrect."})

    def test_invalid_body_does_not_echo_password(self):
        for body in [{}, {"email": "test@test.com"}, {**LOGIN, "email": "invalid"}, {**LOGIN, "password": ""}, {**LOGIN, "password": "é" * 37}]:
            with self.subTest(body=body):
                response = self.client.post("/login", json=body)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json(), {"detail": "Vérifiez les champs du formulaire."})

    def test_missing_or_malformed_token(self):
        for headers in [{}, {"Authorization": "Bearer invalid"}, {"Authorization": "Basic abc"}]:
            with self.subTest(headers=headers):
                self.assertEqual(self.client.get("/me", headers=headers).status_code, 401)

    def test_expired_modified_and_unsigned_tokens(self):
        now = datetime.now(timezone.utc)
        claims = {"sub": "1", "exp": now + timedelta(hours=1)}
        tokens = [
            jwt.encode({**claims, "exp": now - timedelta(seconds=10)}, SECRET, algorithm="HS256"),
            jwt.encode(claims, "another-signing-key-for-tests-only", algorithm="HS256"),
            jwt.encode(claims, "", algorithm="none"),
            jwt.encode({"sub": "1"}, SECRET, algorithm="HS256"),
            jwt.encode({**claims, "sub": str(2**63)}, SECRET, algorithm="HS256"),
        ]
        for token in tokens:
            with self.subTest():
                self.assertEqual(self.client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code, 401)

    def test_deleted_user_cannot_access_me(self):
        token = self.client.post("/login", json=LOGIN).json()["access_token"]
        with Session(self.engine) as session:
            session.delete(session.get(User, 1))
            session.commit()
        self.assertEqual(self.client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code, 401)

    def test_legacy_seed_hash_and_idempotent_startup(self):
        original = bcrypt.hashpw(b"test", bcrypt.gensalt()).decode()
        with Session(self.engine) as session:
            user = session.get(User, 1)
            user.hashed_password = "\\x" + original.encode().hex()
            session.add(user)
            session.commit()
        database.init_db()
        database.init_db()
        self.assertEqual(self.client.post("/login", json=LOGIN).status_code, 200)
        with Session(self.engine) as session:
            users = session.exec(select(User)).all()
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0].hashed_password, original)

    def test_cors_allows_only_configured_origins(self):
        for origin, expected in [("http://localhost:3000", 200), ("https://other.example", 400)]:
            with self.subTest(origin=origin):
                response = self.client.options("/login", headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization",
                })
                self.assertEqual(response.status_code, expected)
                if expected == 200:
                    self.assertEqual(response.headers["access-control-allow-origin"], origin)
                else:
                    self.assertNotIn("access-control-allow-origin", response.headers)

    def test_missing_secret_does_not_issue_token(self):
        with patch.dict(os.environ, {"JWT_SECRET_KEY": ""}):
            response = self.client.post("/login", json=LOGIN)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("access_token", response.json())

    def test_database_error_is_generic(self):
        def unavailable():
            raise OperationalError("private-query", {}, Exception("private-error"))

        app.dependency_overrides[database.get_session] = unavailable
        response = self.client.post("/login", json=LOGIN)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "Service temporairement indisponible."})


if __name__ == "__main__":
    unittest.main()

import os
import uuid
import shutil
from typing import Dict

import pytest
import sys

# Ensure project root is importable
if "/workspace" not in sys.path:
    sys.path.insert(0, "/workspace")
import jwt
from fastapi.testclient import TestClient


# Ensure a clean SQLite database for tests
TEST_DB_PATH = "/workspace/test.db"


@pytest.fixture(scope="session", autouse=True)
def _set_env_before_import() -> None:
    # Remove previous test DB
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # Required settings for the app
    os.environ["PROJECT_NAME"] = "Smart Finances - Tests"
    os.environ["API_V1_STR"] = "/api/v1"
    os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
    os.environ["SUPABASE_URL"] = "http://localhost"
    os.environ["SUPABASE_KEY"] = "test-supabase-key"
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
    os.environ["BACKEND_CORS_ORIGINS"] = '["*"]'
    os.environ["SECRET_KEY"] = "test-secret-key"


@pytest.fixture(scope="session")
def client() -> TestClient:
    # Import after env vars are set so the app is configured correctly
    from app import app as fastapi_app
    test_client = TestClient(fastapi_app)
    return test_client


@pytest.fixture()
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture()
def auth_headers(user_id: uuid.UUID) -> Dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, os.environ["JWT_SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def create_registered_user(client: TestClient, auth_headers: Dict[str, str]):
    def _create(name: str, email: str, **extra):
        payload = {
            "name": name,
            "email": email,
            "phone_number": extra.get("phone_number"),
            "currency": extra.get("currency"),
            "language": extra.get("language"),
            "profile_image": extra.get("profile_image"),
        }
        return client.post("/api/v1/users", json=payload, headers=auth_headers)

    return _create


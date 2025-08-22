import os
import uuid
import shutil
from typing import Dict

import pytest
import sys

# Ensure project root is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import jwt
from fastapi.testclient import TestClient


# Note: DB path is created per session (and per worker) inside the fixture below


@pytest.fixture(scope="session", autouse=True)
def _set_env_before_import() -> None:
    # Create a unique temporary directory per session (and effectively per worker)
    import tempfile

    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    pid = os.getpid()
    temp_dir = tempfile.mkdtemp(prefix=f"sf_tests_{worker_id}_{pid}_")
    db_path = os.path.join(temp_dir, "test.db")

    # Required settings for the app
    os.environ["PROJECT_NAME"] = "Smart Finances - Tests"
    os.environ["API_V1_STR"] = "/api/v1"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SUPABASE_URL"] = "http://localhost"
    os.environ["SUPABASE_KEY"] = "test-supabase-key"
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
    os.environ["BACKEND_CORS_ORIGINS"] = '["*"]'
    os.environ["SECRET_KEY"] = "test-secret-key"

    # Teardown: remove the temporary directory and DB after the session
    try:
        yield
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


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


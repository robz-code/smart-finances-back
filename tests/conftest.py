import os
import shutil
import sys
import uuid
from typing import Dict

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

# Ensure project root is importable before application modules are loaded
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config.db_base import Base


@pytest.fixture(scope="session", autouse=True)
def _configure_test_environment() -> None:
    """Set testing environment variables and reset cached configuration."""
    import tempfile

    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    pid = os.getpid()
    temp_dir = tempfile.mkdtemp(prefix=f"sf_tests_{worker_id}_{pid}_")
    db_path = os.path.join(temp_dir, "test.db")

    os.environ["PROJECT_NAME"] = "Smart Finances - Tests"
    os.environ["API_V1_STR"] = "/api/v1"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SUPABASE_URL"] = ""
    os.environ["SUPABASE_KEY"] = ""
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
    os.environ["BACKEND_CORS_ORIGINS"] = '["*"]'
    os.environ["SECRET_KEY"] = "test-secret-key"

    from app.config.database import reset_database_state
    from app.config.settings import reload_settings

    reload_settings()
    reset_database_state()

    try:
        yield
    finally:
        try:
            from app.config.database import reset_database_state as reset_db

            reset_db()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def db_engine(_configure_test_environment):
    """Create a SQLite engine dedicated to the test session."""
    from app.config.database import get_engine

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    """Provide a sessionmaker bound to the test database engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture(autouse=True)
def _reset_database_state(db_engine):
    """Ensure each test runs against a clean database schema."""
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)
    yield


@pytest.fixture(scope="session")
def client(db_session_factory):
    """FastAPI test client configured to use the test database."""
    from app import app as fastapi_app
    from app.config.database import get_db

    def _get_test_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _get_test_db
    test_client = TestClient(fastapi_app)
    try:
        yield test_client
    finally:
        test_client.close()
        fastapi_app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture()
def auth_headers(user_id: uuid.UUID) -> Dict[str, str]:
    token = jwt.encode(
        {"sub": str(user_id)}, os.environ["JWT_SECRET_KEY"], algorithm="HS256"
    )
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

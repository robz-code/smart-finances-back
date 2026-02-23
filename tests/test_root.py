import pytest
from app.config.settings import get_settings

def test_root_endpoint_access(client):
    """Test root endpoint access based on DEBUG setting."""
    settings = get_settings()
    resp = client.get("/")
    
    if settings.DEBUG:
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"].startswith("Welcome to Smart Finances API")
    else:
        assert resp.status_code == 404

def test_docs_access(client):
    """Test documentation access based on DEBUG setting."""
    settings = get_settings()
    
    # Check /docs
    resp_docs = client.get("/docs")
    # Check /redoc
    resp_redoc = client.get("/redoc")
    # Check openapi.json
    api_str = settings.API_V1_STR
    resp_openapi = client.get(f"{api_str}/openapi.json")
    
    if settings.DEBUG:
        assert resp_docs.status_code == 200
        assert resp_redoc.status_code == 200
        assert resp_openapi.status_code == 200
    else:
        # When docs_url=None in FastAPI, it returns 404
        assert resp_docs.status_code == 404
        assert resp_redoc.status_code == 404
        assert resp_openapi.status_code == 404

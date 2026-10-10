"""Tests for VYOM+ backend health and root endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint responds with basic system information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "VYOM+"
    assert data["status"] == "online"
    assert "tagline" in data


def test_health_check_endpoint():
    """Verify health check endpoint returns 200 and correct status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "VYOM+"
    assert "version" in data
    assert "environment" in data
    assert "gemini_configured" in data
    assert "gemini_model" in data
    # Ensure sensitive information is never leaked in health payload
    assert "gemini_api_key" not in data
    assert "api_key" not in data


def test_api_health_alias():
    """Verify /api/health alias endpoint matches /health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

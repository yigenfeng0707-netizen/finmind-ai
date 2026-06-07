"""Unit tests for API routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        # We test the API structure rather than full integration
        from fastapi import FastAPI
        from api.routes import router
        
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "agents" in data

    def test_api_info_endpoint(self, client):
        """Test API info endpoint."""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "FinMind AI API"
        assert "endpoints" in data

    def test_invalid_symbol(self, client):
        """Test that invalid symbols are rejected."""
        response = client.get("/api/v1/analyze/INVALIDSYMBOL123")
        assert response.status_code == 400

    def test_agents_status_endpoint(self, client):
        """Test agents status endpoint."""
        response = client.get("/api/v1/agents/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "agents" in data

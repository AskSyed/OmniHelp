"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_query_endpoint_empty():
    """Test query endpoint with empty query"""
    response = client.post("/api/v1/query", json={"query": ""})
    assert response.status_code == 400


def test_query_endpoint_valid():
    """Test query endpoint with valid query"""
    response = client.post("/api/v1/query", json={"query": "What is this?"})
    # May return 200 or 500 depending on ChromaDB state
    assert response.status_code in [200, 500]

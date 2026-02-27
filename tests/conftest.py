"""
Pytest configuration and fixtures for FastAPI app tests.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a TestClient instance for API testing."""
    return TestClient(app)


@pytest.fixture
def sample_email():
    """Provide a sample email for testing."""
    return "test@mergington.edu"

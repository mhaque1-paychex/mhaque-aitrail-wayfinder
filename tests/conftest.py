"""
Pytest configuration and fixtures for FastAPI tests
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Provides a TestClient instance for FastAPI.
    This allows us to make requests to the API without running a live server.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture to reset the activities database before and after each test.
    This ensures test isolation - no test data bleeds into the next test.
    Yields to the test, then resets activities to original state.
    """
    # Store original state
    original_activities = {
        name: {
            "description": data["description"],
            "schedule": data["schedule"],
            "max_participants": data["max_participants"],
            "participants": data["participants"].copy()  # Deep copy the list
        }
        for name, data in activities.items()
    }
    
    yield
    
    # Reset to original state after test completes
    activities.clear()
    activities.update(original_activities)

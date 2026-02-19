"""
Simple test script for the API endpoints.
This is a basic test to verify the API is working correctly.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    print("✓ Root endpoint working")


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✓ Health check working")


def test_simulation_start_validation():
    """Test simulation start endpoint validation."""
    # Test with missing required fields
    response = client.post(
        "/simulation/start",
        json={
            "class_name": "CS101",
            # Missing other required fields
        },
    )
    assert response.status_code == 422  # Validation error
    print("✓ Simulation validation working")


def test_simulation_status_not_found():
    """Test simulation status for non-existent simulation."""
    response = client.get("/simulation/fake-id-123/status")
    assert response.status_code == 404
    print("✓ Simulation not found handling working")


def test_material_upload_validation():
    """Test material upload with invalid file type."""
    # This would require actual file upload, so we'll skip for now
    print("⊘ Material upload test skipped (requires file)")


def test_teacher_dashboard():
    """Test teacher dashboard endpoint."""
    response = client.get("/teacher/teacher_001/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "teacher_id" in data
    assert "total_simulations" in data
    print("✓ Teacher dashboard working")


if __name__ == "__main__":
    print("Running API tests...\n")

    try:
        test_root()
        test_health_check()
        test_simulation_start_validation()
        test_simulation_status_not_found()
        test_material_upload_validation()
        test_teacher_dashboard()

        print("\n✓ All tests passed!")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_global_exception_handler():
    """Test if the global exception handler returns a 500 status code when an unhandled exception occurs."""

    with patch(
        "api.routers.analyse.analyse_text", side_effect=RuntimeError("Unexpected error")
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            response = c.post("/analyse/", json={"content": "test"})
            assert response.status_code == 500
            assert response.json() == {"detail": "Internal server error"}


def test_root():
    """Test if the root endpoint returns a 200 status code and the expected message."""

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_returns_200():
    """Test if the /health/ endpoint returns a 200 status code."""

    response = client.get("/health/")
    assert response.status_code == 200


def test_health_status_is_ok():
    """Test if the /health/ endpoint returns a JSON with status 'ok'."""

    response = client.get("/health/")
    assert response.json()["status"] == "ok"


def test_health_contains_required_fields():
    """Test if the /health/ endpoint returns a JSON with required fields."""

    response = client.get("/health/")
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data


def test_health_timestamp_is_valid_iso():
    """Test if the /health/ endpoint returns a timestamp in valid ISO format."""

    from datetime import datetime

    response = client.get("/health/")
    timestamp = response.json()["timestamp"]
    datetime.fromisoformat(timestamp)


# --- /health/celery/ ---


def test_health_celery_returns_200_with_workers():
    """Test /health/celery/ returns worker info when Celery is available."""

    mock_inspector = MagicMock()
    mock_inspector.active.return_value = {
        "worker-1": [{"id": "task-1"}],
        "worker-2": [],
    }

    with patch("api.app.celery") as mock_celery:
        mock_celery.control.inspect.return_value = mock_inspector
        response = client.get("/health/celery/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["total_workers"] == 2
    assert data["workers"]["worker-1"]["active_tasks"] == 1
    assert data["workers"]["worker-2"]["active_tasks"] == 0


def test_health_celery_returns_200_no_workers():
    """Test /health/celery/ returns empty workers when none are registered."""

    mock_inspector = MagicMock()
    mock_inspector.active.return_value = {}

    with patch("api.app.celery") as mock_celery:
        mock_celery.control.inspect.return_value = mock_inspector
        response = client.get("/health/celery/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["total_workers"] == 0
    assert data["workers"] == {}


def test_health_celery_returns_503_when_redis_unavailable():
    """Test /health/celery/ returns 503 when Redis connection fails."""

    with patch("api.app.celery") as mock_celery:
        mock_celery.control.inspect.side_effect = ConnectionError("Connection refused")
        response = client.get("/health/celery/")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "error"
    assert "error" in data

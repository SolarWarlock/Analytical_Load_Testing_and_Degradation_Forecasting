from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "X-Event-Loop-Lag" in response.headers


def test_normal_workload():
    response = client.get("/workload/normal")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

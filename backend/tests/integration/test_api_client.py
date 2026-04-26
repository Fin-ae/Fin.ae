from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_integration_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_integration_get_policies():
    response = client.get("/api/policies")
    assert response.status_code == 200
    data = response.json()
    assert "policies" in data
    assert "count" in data

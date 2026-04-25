"""Health endpoint tests — GET /api/health"""

import requests


def test_health_returns_200(base_url):
    r = requests.get(f"{base_url}/api/health")
    assert r.status_code == 200


def test_health_body_shape(base_url):
    data = requests.get(f"{base_url}/api/health").json()
    assert data["status"] == "ok"
    assert data["service"] == "finae-api"


def test_health_content_type_is_json(base_url):
    r = requests.get(f"{base_url}/api/health")
    assert "application/json" in r.headers.get("Content-Type", "")

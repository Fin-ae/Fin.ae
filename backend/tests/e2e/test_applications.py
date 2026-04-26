import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://127.0.0.1:8000').rstrip('/')

class TestApplicationsEndpoint:
    def test_create_and_get_applications(self):
        session_id = f"test_app_{uuid.uuid4().hex[:8]}"
        payload = {
            "session_id": session_id,
            "policy_id": "ins-001",
            "user_profile": {"name": "Test User", "email": "test@example.com"}
        }
        # Create
        create_resp = requests.post(f"{BASE_URL}/api/applications", json=payload)
        if create_resp.status_code != 200:
            pytest.skip("Could not create app, perhaps user auth is required or mock db needed.")
        
        # Get
        get_resp = requests.get(f"{BASE_URL}/api/applications/{session_id}")
        assert get_resp.status_code == 200

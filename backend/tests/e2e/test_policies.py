import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://127.0.0.1:8000').rstrip('/')

class TestPoliciesEndpoint:
    def test_get_all_policies(self):
        response = requests.get(f"{BASE_URL}/api/policies")
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert "count" in data
        assert data["count"] > 0
    
    def test_filter_by_category(self):
        response = requests.get(f"{BASE_URL}/api/policies", params={"category": "insurance"})
        assert response.status_code == 200
        for policy in response.json()["policies"]:
            assert policy["category"] == "insurance"

    def test_get_single_policy(self):
        response = requests.get(f"{BASE_URL}/api/policies/ins-001")
        assert response.status_code == 200
        assert response.json()["policy"]["policy_id"] == "ins-001"

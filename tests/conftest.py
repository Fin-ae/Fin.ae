import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def session_id():
    return f"test_{uuid.uuid4().hex[:10]}"


@pytest.fixture(scope="session")
def http():
    """Configured requests session with base URL and JSON content-type."""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def known_policy_ids():
    return ["ins-001", "ins-002", "ins-003", "loan-001", "loan-002", "loan-003",
            "cc-001", "cc-002", "inv-001", "inv-002", "ba-001", "ba-002"]


@pytest.fixture
def sample_user_profile():
    return {
        "name": "Ahmed Al Mansoori",
        "age": 32,
        "nationality": "UAE",
        "residency_status": "UAE resident",
        "monthly_salary": 18000,
        "employment_type": "salaried",
        "financial_goal": "insurance",
        "risk_appetite": "moderate",
        "sharia_compliant": False,
        "email": "ahmed@example.com",
        "phone": "+971501234567",
    }

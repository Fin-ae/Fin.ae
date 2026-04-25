"""
Application tracking tests — full lifecycle:
  create → retrieve → update status → status history integrity
"""

import uuid
import requests
import pytest


def _sid():
    return f"app_test_{uuid.uuid4().hex[:10]}"


VALID_STATUSES = ["submitted", "under_review", "approved", "rejected", "withdrawn"]


@pytest.fixture
def created_application(base_url, sample_user_profile):
    """Creates a fresh application and returns (session_id, application_id, response data)."""
    sid = _sid()
    payload = {
        "session_id": sid,
        "policy_id": "ins-001",
        "user_profile": sample_user_profile,
    }
    data = requests.post(f"{base_url}/api/applications", json=payload).json()
    return sid, data["application"]["application_id"], data["application"]


class TestCreateApplication:
    def test_create_returns_200(self, base_url, sample_user_profile):
        r = requests.post(f"{base_url}/api/applications",
                          json={"session_id": _sid(), "policy_id": "ins-001",
                                "user_profile": sample_user_profile})
        assert r.status_code == 200

    def test_response_has_application_key(self, base_url, sample_user_profile):
        data = requests.post(f"{base_url}/api/applications",
                             json={"session_id": _sid(), "policy_id": "ins-001",
                                   "user_profile": sample_user_profile}).json()
        assert "application" in data

    def test_application_fields_present(self, base_url, sample_user_profile):
        required = {"application_id", "session_id", "policy_id", "policy_name",
                    "provider", "category", "user_profile", "status",
                    "status_history", "created_at"}
        app = requests.post(f"{base_url}/api/applications",
                            json={"session_id": _sid(), "policy_id": "ins-001",
                                  "user_profile": sample_user_profile}).json()["application"]
        missing = required - app.keys()
        assert not missing, f"Missing fields: {missing}"

    def test_initial_status_is_submitted(self, base_url, sample_user_profile):
        app = requests.post(f"{base_url}/api/applications",
                            json={"session_id": _sid(), "policy_id": "ins-001",
                                  "user_profile": sample_user_profile}).json()["application"]
        assert app["status"] == "submitted"

    def test_application_id_has_app_prefix(self, base_url, sample_user_profile):
        app = requests.post(f"{base_url}/api/applications",
                            json={"session_id": _sid(), "policy_id": "cc-001",
                                  "user_profile": sample_user_profile}).json()["application"]
        assert app["application_id"].startswith("APP-")

    def test_policy_metadata_copied_to_application(self, base_url, sample_user_profile):
        app = requests.post(f"{base_url}/api/applications",
                            json={"session_id": _sid(), "policy_id": "ins-001",
                                  "user_profile": sample_user_profile}).json()["application"]
        assert app["policy_name"] == "ADNIC Premium Health Cover"
        assert app["category"] == "insurance"

    def test_user_profile_stored_correctly(self, base_url, sample_user_profile):
        app = requests.post(f"{base_url}/api/applications",
                            json={"session_id": _sid(), "policy_id": "ins-001",
                                  "user_profile": sample_user_profile}).json()["application"]
        assert app["user_profile"]["name"] == sample_user_profile["name"]
        assert app["user_profile"]["monthly_salary"] == sample_user_profile["monthly_salary"]

    def test_invalid_policy_returns_404(self, base_url, sample_user_profile):
        r = requests.post(f"{base_url}/api/applications",
                          json={"session_id": _sid(), "policy_id": "nonexistent-xyz",
                                "user_profile": sample_user_profile})
        assert r.status_code == 404

    @pytest.mark.parametrize("policy_id", ["ins-001", "loan-001", "cc-001", "inv-001", "ba-001"])
    def test_can_apply_to_each_category(self, base_url, sample_user_profile, policy_id):
        r = requests.post(f"{base_url}/api/applications",
                          json={"session_id": _sid(), "policy_id": policy_id,
                                "user_profile": sample_user_profile})
        assert r.status_code == 200


class TestGetApplications:
    def test_get_returns_200(self, base_url, created_application):
        sid, _, _ = created_application
        r = requests.get(f"{base_url}/api/applications/{sid}")
        assert r.status_code == 200

    def test_response_shape(self, base_url, created_application):
        sid, _, _ = created_application
        data = requests.get(f"{base_url}/api/applications/{sid}").json()
        assert "applications" in data
        assert "count" in data

    def test_created_application_appears_in_list(self, base_url, created_application):
        sid, app_id, _ = created_application
        data = requests.get(f"{base_url}/api/applications/{sid}").json()
        assert data["count"] >= 1
        ids = [a["application_id"] for a in data["applications"]]
        assert app_id in ids

    def test_multiple_applications_for_same_session(self, base_url, sample_user_profile):
        sid = _sid()
        for pid in ["ins-001", "loan-001"]:
            requests.post(f"{base_url}/api/applications",
                          json={"session_id": sid, "policy_id": pid, "user_profile": sample_user_profile})
        data = requests.get(f"{base_url}/api/applications/{sid}").json()
        assert data["count"] == 2

    def test_empty_session_returns_zero_count(self, base_url):
        data = requests.get(f"{base_url}/api/applications/ghost_{uuid.uuid4().hex}").json()
        assert data["count"] == 0
        assert data["applications"] == []

    def test_sessions_are_isolated(self, base_url, sample_user_profile):
        sid_a, sid_b = _sid(), _sid()
        requests.post(f"{base_url}/api/applications",
                      json={"session_id": sid_a, "policy_id": "ins-001", "user_profile": sample_user_profile})
        data_b = requests.get(f"{base_url}/api/applications/{sid_b}").json()
        assert data_b["count"] == 0


class TestUpdateApplicationStatus:
    def test_update_status_returns_200(self, base_url, created_application):
        _, app_id, _ = created_application
        r = requests.patch(f"{base_url}/api/applications/{app_id}",
                           json={"status": "under_review"})
        assert r.status_code == 200

    def test_status_reflects_update(self, base_url, created_application):
        _, app_id, _ = created_application
        requests.patch(f"{base_url}/api/applications/{app_id}", json={"status": "approved"})
        app = requests.patch(f"{base_url}/api/applications/{app_id}",
                             json={"status": "approved"}).json()["application"]
        assert app["status"] == "approved"

    def test_status_history_grows_on_each_update(self, base_url, sample_user_profile):
        sid = _sid()
        app = requests.post(f"{base_url}/api/applications",
                            json={"session_id": sid, "policy_id": "loan-001",
                                  "user_profile": sample_user_profile}).json()["application"]
        app_id = app["application_id"]
        assert len(app["status_history"]) == 1

        requests.patch(f"{base_url}/api/applications/{app_id}", json={"status": "under_review"})
        app2 = requests.patch(f"{base_url}/api/applications/{app_id}",
                              json={"status": "approved"}).json()["application"]
        assert len(app2["status_history"]) >= 3

    def test_status_history_entry_has_required_fields(self, base_url, created_application):
        _, app_id, app = created_application
        entry = app["status_history"][0]
        assert "status" in entry
        assert "timestamp" in entry
        assert "note" in entry

    def test_first_history_entry_is_submitted(self, base_url, created_application):
        _, _, app = created_application
        assert app["status_history"][0]["status"] == "submitted"

    def test_update_nonexistent_application_returns_404(self, base_url):
        r = requests.patch(f"{base_url}/api/applications/APP-DOESNOTEXIST",
                           json={"status": "approved"})
        assert r.status_code == 404

    @pytest.mark.parametrize("status", VALID_STATUSES)
    def test_all_standard_statuses_accepted(self, base_url, sample_user_profile, status):
        sid = _sid()
        app = requests.post(f"{base_url}/api/applications",
                            json={"session_id": sid, "policy_id": "cc-001",
                                  "user_profile": sample_user_profile}).json()["application"]
        r = requests.patch(f"{base_url}/api/applications/{app['application_id']}",
                           json={"status": status})
        assert r.status_code == 200
        assert r.json()["application"]["status"] == status

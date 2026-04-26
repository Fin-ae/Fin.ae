"""Policy endpoint tests — GET /api/policies and GET /api/policies/{id}"""

import requests
import pytest

CATEGORIES = ["insurance", "loan", "credit_card", "investment", "bank_account"]
RISK_LEVELS = ["low", "medium", "high"]


class TestGetAllPolicies:
    def test_returns_200(self, base_url):
        r = requests.get(f"{base_url}/api/policies")
        assert r.status_code == 200

    def test_response_has_required_keys(self, base_url):
        data = requests.get(f"{base_url}/api/policies").json()
        assert "policies" in data
        assert "count" in data

    def test_total_seed_count_is_12(self, base_url):
        data = requests.get(f"{base_url}/api/policies").json()
        assert data["count"] == 12
        assert len(data["policies"]) == 12

    def test_each_policy_has_required_fields(self, base_url):
        required = {"policy_id", "category", "name", "provider", "min_salary",
                    "min_age", "max_age", "risk_level", "sharia_compliant", "rating"}
        policies = requests.get(f"{base_url}/api/policies").json()["policies"]
        for p in policies:
            missing = required - p.keys()
            assert not missing, f"Policy {p.get('policy_id')} missing: {missing}"


class TestCategoryFilter:
    @pytest.mark.parametrize("category", CATEGORIES)
    def test_filter_returns_only_matching_category(self, base_url, category):
        data = requests.get(f"{base_url}/api/policies", params={"category": category}).json()
        for p in data["policies"]:
            assert p["category"] == category

    def test_unknown_category_returns_empty(self, base_url):
        data = requests.get(f"{base_url}/api/policies", params={"category": "nonexistent"}).json()
        assert data["count"] == 0

    def test_insurance_has_at_least_3(self, base_url):
        data = requests.get(f"{base_url}/api/policies", params={"category": "insurance"}).json()
        assert data["count"] >= 3

    def test_loan_has_at_least_3(self, base_url):
        data = requests.get(f"{base_url}/api/policies", params={"category": "loan"}).json()
        assert data["count"] >= 3


class TestShariaFilter:
    def test_sharia_true_returns_only_compliant(self, base_url):
        data = requests.get(f"{base_url}/api/policies", params={"sharia_compliant": "true"}).json()
        assert data["count"] > 0
        for p in data["policies"]:
            assert p["sharia_compliant"] is True

    def test_sharia_false_returns_only_non_compliant(self, base_url):
        data = requests.get(f"{base_url}/api/policies", params={"sharia_compliant": "false"}).json()
        for p in data["policies"]:
            assert p["sharia_compliant"] is False


class TestRiskLevelFilter:
    @pytest.mark.parametrize("level", RISK_LEVELS)
    def test_risk_filter_returns_correct_level(self, base_url, level):
        data = requests.get(f"{base_url}/api/policies", params={"risk_level": level}).json()
        for p in data["policies"]:
            assert p["risk_level"] == level


class TestMinSalaryFilter:
    def test_salary_filter_excludes_high_minimums(self, base_url):
        # Only policies with min_salary <= 5000 should appear
        data = requests.get(f"{base_url}/api/policies", params={"min_salary": 5000}).json()
        for p in data["policies"]:
            assert p["min_salary"] <= 5000

    def test_high_salary_returns_all_policies(self, base_url):
        data = requests.get(f"{base_url}/api/policies", params={"min_salary": 999999}).json()
        assert data["count"] == 12


class TestGetSinglePolicy:
    def test_known_policy_returns_200(self, base_url, known_policy_ids):
        for pid in known_policy_ids[:3]:
            r = requests.get(f"{base_url}/api/policies/{pid}")
            assert r.status_code == 200, f"Expected 200 for {pid}"

    def test_response_wraps_in_policy_key(self, base_url):
        data = requests.get(f"{base_url}/api/policies/ins-001").json()
        assert "policy" in data
        assert data["policy"]["policy_id"] == "ins-001"

    def test_insurance_policy_data_correct(self, base_url):
        p = requests.get(f"{base_url}/api/policies/ins-001").json()["policy"]
        assert p["name"] == "ADNIC Premium Health Cover"
        assert p["category"] == "insurance"
        assert p["sub_category"] == "health"

    def test_nonexistent_policy_returns_404(self, base_url):
        r = requests.get(f"{base_url}/api/policies/does-not-exist")
        assert r.status_code == 404

    def test_all_seed_policies_retrievable(self, base_url, known_policy_ids):
        for pid in known_policy_ids:
            r = requests.get(f"{base_url}/api/policies/{pid}")
            assert r.status_code == 200, f"Seed policy {pid} not found"


class TestCompareEndpoint:
    def test_compare_two_policies_returns_200(self, base_url):
        r = requests.post(f"{base_url}/api/policies/compare",
                          json={"policy_ids": ["ins-001", "ins-002"]})
        assert r.status_code == 200

    def test_compare_returns_both_policies(self, base_url):
        data = requests.post(f"{base_url}/api/policies/compare",
                             json={"policy_ids": ["ins-001", "loan-001"]}).json()
        returned_ids = {p["policy_id"] for p in data["policies"]}
        assert "ins-001" in returned_ids
        assert "loan-001" in returned_ids

    def test_compare_up_to_four_is_allowed(self, base_url):
        r = requests.post(f"{base_url}/api/policies/compare",
                          json={"policy_ids": ["ins-001", "ins-002", "loan-001", "cc-001"]})
        assert r.status_code == 200
        assert r.json()["count"] == 4

    def test_compare_fewer_than_two_returns_400(self, base_url):
        r = requests.post(f"{base_url}/api/policies/compare",
                          json={"policy_ids": ["ins-001"]})
        assert r.status_code == 400

    def test_compare_more_than_four_returns_400(self, base_url):
        r = requests.post(f"{base_url}/api/policies/compare",
                          json={"policy_ids": ["ins-001", "ins-002", "ins-003", "loan-001", "loan-002"]})
        assert r.status_code == 400

    def test_compare_with_all_invalid_ids_returns_404(self, base_url):
        r = requests.post(f"{base_url}/api/policies/compare",
                          json={"policy_ids": ["fake-001", "fake-002"]})
        assert r.status_code == 404

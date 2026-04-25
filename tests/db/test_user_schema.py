"""
User/data schema validation tests.

Validates the data contracts the API produces and consumes:
  - Policy schema (fields, types, constraints)
  - User profile schema (extracted from chat)
  - Application schema
  - News schema
  - In-memory store consistency (no duplicate IDs, referential integrity)
"""

import re
import uuid
import requests
import pytest


# ─── Helpers ──────────────────────────────────────────────────────────────────

def all_policies(base_url):
    return requests.get(f"{base_url}/api/policies").json()["policies"]


def all_news(base_url):
    return requests.get(f"{base_url}/api/news").json()["news"]


# ─── Policy Schema ─────────────────────────────────────────────────────────────

class TestPolicySchema:
    """Validates the shape and types of every policy in the seed store."""

    def test_policy_id_is_nonempty_string(self, base_url):
        for p in all_policies(base_url):
            assert isinstance(p["policy_id"], str) and p["policy_id"]

    def test_policy_ids_are_unique(self, base_url):
        ids = [p["policy_id"] for p in all_policies(base_url)]
        assert len(ids) == len(set(ids)), "Duplicate policy_id detected"

    def test_policy_id_format(self, base_url):
        """policy_id must match <prefix>-<digits> e.g. ins-001, loan-002."""
        pattern = re.compile(r"^[a-z_]+-\d{3}$")
        for p in all_policies(base_url):
            assert pattern.match(p["policy_id"]), f"Bad policy_id format: {p['policy_id']}"

    def test_category_is_valid_enum(self, base_url):
        valid = {"insurance", "loan", "credit_card", "investment", "bank_account"}
        for p in all_policies(base_url):
            assert p["category"] in valid, f"Unknown category: {p['category']} in {p['policy_id']}"

    def test_risk_level_is_valid_enum(self, base_url):
        valid = {"low", "medium", "high"}
        for p in all_policies(base_url):
            assert p["risk_level"] in valid, f"Unknown risk_level: {p['risk_level']} in {p['policy_id']}"

    def test_sharia_compliant_is_boolean(self, base_url):
        for p in all_policies(base_url):
            assert isinstance(p["sharia_compliant"], bool), \
                f"sharia_compliant must be bool in {p['policy_id']}"

    def test_min_salary_is_non_negative_int(self, base_url):
        for p in all_policies(base_url):
            assert isinstance(p["min_salary"], int) and p["min_salary"] >= 0, \
                f"Invalid min_salary in {p['policy_id']}"

    def test_age_bounds_are_valid(self, base_url):
        for p in all_policies(base_url):
            assert 0 < p["min_age"] < p["max_age"], \
                f"Age bounds invalid in {p['policy_id']}: min={p['min_age']} max={p['max_age']}"

    def test_rating_is_between_0_and_5(self, base_url):
        for p in all_policies(base_url):
            assert 0 <= p["rating"] <= 5, f"Rating out of range in {p['policy_id']}: {p['rating']}"

    def test_name_and_provider_are_nonempty_strings(self, base_url):
        for p in all_policies(base_url):
            assert isinstance(p["name"], str) and p["name"]
            assert isinstance(p["provider"], str) and p["provider"]

    def test_benefits_is_list_of_strings(self, base_url):
        for p in all_policies(base_url):
            assert isinstance(p["benefits"], list), f"benefits must be list in {p['policy_id']}"
            for b in p["benefits"]:
                assert isinstance(b, str), f"benefit item must be str in {p['policy_id']}"

    def test_features_is_dict(self, base_url):
        for p in all_policies(base_url):
            assert isinstance(p["features"], dict), f"features must be dict in {p['policy_id']}"

    def test_sharia_policies_are_subset_of_all(self, base_url):
        all_ids = {p["policy_id"] for p in all_policies(base_url)}
        sharia_ids = {p["policy_id"] for p in all_policies(base_url) if p["sharia_compliant"]}
        assert sharia_ids.issubset(all_ids)
        assert len(sharia_ids) >= 1


# ─── News Schema ──────────────────────────────────────────────────────────────

class TestNewsSchema:
    def test_news_ids_are_unique(self, base_url):
        ids = [a["news_id"] for a in all_news(base_url)]
        assert len(ids) == len(set(ids))

    def test_date_format_is_iso(self, base_url):
        """Dates should be YYYY-MM-DD strings."""
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for a in all_news(base_url):
            assert pattern.match(a["date"]), f"Bad date format in {a['news_id']}: {a['date']}"

    def test_title_and_summary_are_nonempty(self, base_url):
        for a in all_news(base_url):
            assert a["title"].strip()
            assert a["summary"].strip()

    def test_source_is_nonempty_string(self, base_url):
        for a in all_news(base_url):
            assert isinstance(a["source"], str) and a["source"]


# ─── User Profile Schema ───────────────────────────────────────────────────────

class TestUserProfileSchema:
    """Validates profiles returned by /api/chat/extract-profile."""

    PROFILE_KEYS = {
        "name", "age", "nationality", "residency_status", "monthly_salary",
        "employment_type", "financial_goal", "risk_appetite",
        "sharia_compliant", "specific_requirements", "completeness_score",
    }

    def _build_profile(self, base_url):
        import time
        sid = f"schema_test_{uuid.uuid4().hex[:10]}"
        msgs = [
            "I need health insurance",
            "My name is Fatima and I am 28 years old",
            "I am a UAE resident and I earn 15000 AED per month",
            "I am salaried and prefer sharia compliant products",
        ]
        for m in msgs:
            requests.post(f"{base_url}/api/chat/message", json={"session_id": sid, "message": m})
            time.sleep(0.4)
        return requests.post(f"{base_url}/api/chat/extract-profile",
                             json={"session_id": sid}).json()["profile"]

    def test_extract_returns_all_expected_keys(self, base_url):
        profile = self._build_profile(base_url)
        missing = self.PROFILE_KEYS - profile.keys()
        assert not missing, f"Profile missing keys: {missing}"

    def test_completeness_score_in_range(self, base_url):
        profile = self._build_profile(base_url)
        score = profile.get("completeness_score")
        assert score is not None
        assert 0 <= score <= 100, f"completeness_score out of range: {score}"

    def test_rich_conversation_yields_high_completeness(self, base_url):
        profile = self._build_profile(base_url)
        assert profile.get("completeness_score", 0) >= 40, \
            "Expected completeness ≥ 40 after 4 informative messages"

    def test_sharia_compliant_is_bool_or_none(self, base_url):
        profile = self._build_profile(base_url)
        val = profile.get("sharia_compliant")
        assert val is None or isinstance(val, bool), \
            f"sharia_compliant must be bool or null, got {type(val)}"

    def test_monthly_salary_is_numeric_or_none(self, base_url):
        profile = self._build_profile(base_url)
        val = profile.get("monthly_salary")
        assert val is None or isinstance(val, (int, float)), \
            f"monthly_salary must be numeric or null, got {type(val)}"

    def test_age_is_positive_int_or_none(self, base_url):
        profile = self._build_profile(base_url)
        val = profile.get("age")
        assert val is None or (isinstance(val, int) and val > 0), \
            f"age must be positive int or null, got {val}"


# ─── Application Schema ───────────────────────────────────────────────────────

class TestApplicationSchema:
    """Validates the schema of created and retrieved applications."""

    REQUIRED_APP_FIELDS = {
        "application_id", "session_id", "policy_id", "policy_name",
        "provider", "category", "user_profile", "status",
        "status_history", "created_at",
    }

    REQUIRED_HISTORY_FIELDS = {"status", "timestamp", "note"}

    def _create(self, base_url, sample_user_profile, policy_id="ins-001"):
        sid = f"schema_{uuid.uuid4().hex[:10]}"
        return requests.post(f"{base_url}/api/applications",
                             json={"session_id": sid, "policy_id": policy_id,
                                   "user_profile": sample_user_profile}).json()["application"]

    def test_all_required_fields_present(self, base_url, sample_user_profile):
        app = self._create(base_url, sample_user_profile)
        missing = self.REQUIRED_APP_FIELDS - app.keys()
        assert not missing, f"Application missing: {missing}"

    def test_application_id_uppercase_hex(self, base_url, sample_user_profile):
        app = self._create(base_url, sample_user_profile)
        assert re.match(r"^APP-[A-F0-9]{8}$", app["application_id"]), \
            f"Unexpected application_id format: {app['application_id']}"

    def test_category_matches_policy(self, base_url, sample_user_profile):
        app = self._create(base_url, sample_user_profile, policy_id="loan-001")
        assert app["category"] == "loan"

    def test_created_at_is_iso_datetime(self, base_url, sample_user_profile):
        app = self._create(base_url, sample_user_profile)
        # ISO 8601 datetime with timezone
        assert "T" in app["created_at"] and ("Z" in app["created_at"] or "+" in app["created_at"])

    def test_status_history_has_one_entry_on_create(self, base_url, sample_user_profile):
        app = self._create(base_url, sample_user_profile)
        assert len(app["status_history"]) == 1

    def test_status_history_entry_shape(self, base_url, sample_user_profile):
        app = self._create(base_url, sample_user_profile)
        entry = app["status_history"][0]
        missing = self.REQUIRED_HISTORY_FIELDS - entry.keys()
        assert not missing, f"History entry missing: {missing}"

    def test_status_history_timestamp_is_iso(self, base_url, sample_user_profile):
        app = self._create(base_url, sample_user_profile)
        ts = app["status_history"][0]["timestamp"]
        assert "T" in ts

    def test_user_profile_stored_as_dict(self, base_url, sample_user_profile):
        app = self._create(base_url, sample_user_profile)
        assert isinstance(app["user_profile"], dict)

    def test_applications_list_schema(self, base_url, sample_user_profile):
        sid = f"list_schema_{uuid.uuid4().hex[:8]}"
        requests.post(f"{base_url}/api/applications",
                      json={"session_id": sid, "policy_id": "ba-001",
                            "user_profile": sample_user_profile})
        data = requests.get(f"{base_url}/api/applications/{sid}").json()
        assert isinstance(data["applications"], list)
        assert isinstance(data["count"], int)
        for app in data["applications"]:
            missing = self.REQUIRED_APP_FIELDS - app.keys()
            assert not missing


# ─── Store Consistency ─────────────────────────────────────────────────────────

class TestStoreConsistency:
    """Cross-entity referential integrity checks."""

    def test_all_policy_ids_are_retrievable(self, base_url, known_policy_ids):
        for pid in known_policy_ids:
            r = requests.get(f"{base_url}/api/policies/{pid}")
            assert r.status_code == 200, f"Seed policy {pid} not individually retrievable"

    def test_application_policy_id_references_valid_policy(self, base_url, sample_user_profile):
        sid = f"ref_{uuid.uuid4().hex[:8]}"
        app = requests.post(f"{base_url}/api/applications",
                            json={"session_id": sid, "policy_id": "cc-001",
                                  "user_profile": sample_user_profile}).json()["application"]
        # The application stores the policy_id — verify it exists in the policy store
        r = requests.get(f"{base_url}/api/policies/{app['policy_id']}")
        assert r.status_code == 200

    def test_count_field_matches_list_length_for_policies(self, base_url):
        data = requests.get(f"{base_url}/api/policies").json()
        assert data["count"] == len(data["policies"])

    def test_count_field_matches_list_length_for_news(self, base_url):
        data = requests.get(f"{base_url}/api/news").json()
        assert data["count"] == len(data["news"])

    def test_count_field_matches_list_length_for_applications(self, base_url, sample_user_profile):
        sid = f"cnt_{uuid.uuid4().hex[:8]}"
        for pid in ["ins-001", "loan-001", "cc-001"]:
            requests.post(f"{base_url}/api/applications",
                          json={"session_id": sid, "policy_id": pid,
                                "user_profile": sample_user_profile})
        data = requests.get(f"{base_url}/api/applications/{sid}").json()
        assert data["count"] == len(data["applications"])

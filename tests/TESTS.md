# Fin-ae Test Suite Documentation

## Overview

The `tests/` directory contains the full integration test suite for the Fin-ae backend API. All tests run against a live backend instance using `requests` and `pytest`. There are no mocks — every test exercises real HTTP endpoints against the in-memory store seeded at startup.

Tests are organised into three independent sub-suites that can be run together or in isolation.

```
tests/
├── conftest.py
├── pytest.ini
├── api/
│   ├── test_health.py
│   ├── test_policies.py
│   ├── test_news.py
│   └── test_chat.py
├── application_tracking/
│   └── test_applications.py
└── db/
    └── test_user_schema.py
```

---

## Running the Tests

Start the backend first, then point the suite at it via the environment variable:

```bash
# Start the backend (from repo root)
uvicorn backend.server:app --reload --port 8000

# Run everything
REACT_APP_BACKEND_URL=http://localhost:8000 pytest tests/ -v

# Run one sub-suite
pytest tests/api/
pytest tests/application_tracking/
pytest tests/db/
```

The `pytest.ini` at `tests/pytest.ini` sets `addopts = -v --tb=short` so verbose output and short tracebacks are the default without extra flags.

---

## `conftest.py` — Shared Fixtures

**Path:** `tests/conftest.py`

Central fixture file that every test module inherits automatically. Defines all reusable state so individual test files contain no setup boilerplate.

| Fixture | Scope | Purpose |
|---|---|---|
| `base_url` | session | Reads `REACT_APP_BACKEND_URL` env var (defaults to `http://localhost:8000`). Passed to every test that makes HTTP calls. |
| `session_id` | function | Generates a unique `test_<hex>` string per test. Used wherever an isolated chat or application session is needed. |
| `http` | session | A `requests.Session` pre-configured with `Content-Type: application/json`. Available for tests that prefer a session over bare `requests`. |
| `known_policy_ids` | session | The complete list of 12 seed policy IDs (`ins-001` through `ba-002`). Used in completeness and retrievability checks. |
| `sample_user_profile` | function | A fully-populated user profile dict (Ahmed Al Mansoori, 32, salaried, 18 000 AED/month). Used as the default `user_profile` payload in application tests. |

---

## `api/` — API Endpoint Tests

This sub-suite validates every HTTP endpoint for correct status codes, response shapes, and query parameter behaviour. These tests are the first line of defence — if something here fails, the API contract is broken.

---

### `api/test_health.py`

**Endpoint:** `GET /api/health`  
**Tests:** 3

The simplest smoke test in the suite. Verifies the server is reachable and identifies itself correctly before any other test runs.

| Test | What it checks |
|---|---|
| `test_health_returns_200` | Server responds with HTTP 200. |
| `test_health_body_shape` | Response JSON contains `status: "ok"` and `service: "finae-api"`. |
| `test_health_content_type_is_json` | `Content-Type` header is `application/json`. |

**Why it matters:** A failing health check means the backend is not running or not reachable. Every other test will also fail, so this is the first thing to triage.

---

### `api/test_policies.py`

**Endpoints:** `GET /api/policies`, `GET /api/policies/{id}`, `POST /api/policies/compare`  
**Tests:** 25

The largest test file in the `api/` directory. Covers the full policy catalogue surface: listing, filtering, single-record retrieval, and the compare feature.

#### `TestGetAllPolicies` (4 tests)

Validates the unfiltered policy list endpoint.

| Test | What it checks |
|---|---|
| `test_returns_200` | Endpoint is reachable. |
| `test_response_has_required_keys` | Response JSON has both `policies` and `count` keys. |
| `test_total_seed_count_is_12` | Exactly 12 seed policies exist and both list length and `count` field agree. |
| `test_each_policy_has_required_fields` | Every policy object contains the 10 required fields (`policy_id`, `category`, `name`, `provider`, `min_salary`, `min_age`, `max_age`, `risk_level`, `sharia_compliant`, `rating`). |

#### `TestCategoryFilter` (4 tests)

Validates the `?category=` query parameter. Uses `@pytest.mark.parametrize` to run the same filter assertion across all 5 valid categories (`insurance`, `loan`, `credit_card`, `investment`, `bank_account`).

| Test | What it checks |
|---|---|
| `test_filter_returns_only_matching_category` | Parametrized over all 5 categories. Every policy in the result matches the requested category. |
| `test_unknown_category_returns_empty` | An unrecognised category string returns `count: 0`. |
| `test_insurance_has_at_least_3` | Insurance category has at least 3 seed entries. |
| `test_loan_has_at_least_3` | Loan category has at least 3 seed entries. |

#### `TestShariaFilter` (2 tests)

Validates the `?sharia_compliant=` boolean query parameter.

| Test | What it checks |
|---|---|
| `test_sharia_true_returns_only_compliant` | All returned policies have `sharia_compliant: true`. Result is non-empty. |
| `test_sharia_false_returns_only_non_compliant` | All returned policies have `sharia_compliant: false`. |

#### `TestRiskLevelFilter` (3 tests)

Parametrized across `low`, `medium`, `high`. Each run confirms no policies from other risk levels leak through the filter.

#### `TestMinSalaryFilter` (2 tests)

Validates the `?min_salary=` filter, which should exclude policies whose `min_salary` exceeds the supplied value.

| Test | What it checks |
|---|---|
| `test_salary_filter_excludes_high_minimums` | With `min_salary=5000`, every returned policy has `min_salary ≤ 5000`. |
| `test_high_salary_returns_all_policies` | With `min_salary=999999`, all 12 policies are returned. |

#### `TestGetSinglePolicy` (5 tests)

Validates `GET /api/policies/{policy_id}`.

| Test | What it checks |
|---|---|
| `test_known_policy_returns_200` | The first 3 known policy IDs each return 200. |
| `test_response_wraps_in_policy_key` | Response JSON has a `policy` wrapper key and the correct `policy_id`. |
| `test_insurance_policy_data_correct` | `ins-001` returns the exact name, category, and sub-category from seed data. |
| `test_nonexistent_policy_returns_404` | An invalid ID returns 404. |
| `test_all_seed_policies_retrievable` | All 12 known policy IDs return 200 individually. |

#### `TestCompareEndpoint` (6 tests)

Validates `POST /api/policies/compare`.

| Test | What it checks |
|---|---|
| `test_compare_two_policies_returns_200` | Minimum valid comparison (2 IDs) returns 200. |
| `test_compare_returns_both_policies` | Both requested policy IDs appear in the response list. |
| `test_compare_up_to_four_is_allowed` | 4 IDs are accepted and all 4 are returned. |
| `test_compare_fewer_than_two_returns_400` | 1 ID is rejected with 400. |
| `test_compare_more_than_four_returns_400` | 5 IDs are rejected with 400. |
| `test_compare_with_all_invalid_ids_returns_404` | 2 non-existent IDs return 404. |

---

### `api/test_news.py`

**Endpoint:** `GET /api/news`  
**Tests:** 9

Validates the financial news feed — seed count, field completeness, uniqueness, date format, and category filtering.

#### `TestGetAllNews` (6 tests)

| Test | What it checks |
|---|---|
| `test_returns_200` | Endpoint is reachable. |
| `test_response_has_required_keys` | Response has `news` and `count` keys. |
| `test_seed_count_is_6` | Exactly 6 seed articles; list length and `count` agree. |
| `test_each_article_has_required_fields` | Every article has `news_id`, `title`, `summary`, `category`, `date`, `source`. |
| `test_dates_are_strings` | `date` field is a string type on every article. |
| `test_ids_are_unique` | No two articles share the same `news_id`. |

#### `TestNewsCategoryFilter` (3 tests)

| Test | What it checks |
|---|---|
| `test_banking_filter` | `?category=banking` returns only banking articles. |
| `test_insurance_filter` | `?category=insurance` returns only insurance articles. |
| `test_unknown_category_returns_empty` | An unrecognised category returns `count: 0`. |

---

### `api/test_chat.py`

**Endpoints:** `POST /api/chat/message`, `POST /api/chat/open`, `POST /api/chat/extract-profile`  
**Tests:** 11

Validates the AI chat surface — response shapes, multi-turn context retention, session isolation, and profile extraction. Every test generates a fresh session ID via `_new_session()` to prevent cross-test contamination.

#### `TestAvatarChat` (5 tests)

Covers the guided financial onboarding chat (`/api/chat/message`).

| Test | What it checks |
|---|---|
| `test_message_returns_200` | Endpoint accepts a message and returns 200. |
| `test_response_shape` | Response JSON has `response` and `session_id`; `session_id` matches the request. |
| `test_response_is_non_empty_string` | `response` is a non-empty string — the LLM returned content. |
| `test_conversation_context_persists` | A second message on the same session ID returns a valid response (context is maintained in the store). |
| `test_independent_sessions_are_isolated` | A message sent to session B is not affected by prior traffic on session A. |

#### `TestOpenChat` (4 tests)

Covers the open-ended financial Q&A chat (`/api/chat/open`).

| Test | What it checks |
|---|---|
| `test_open_chat_returns_200` | Endpoint is reachable. |
| `test_response_shape` | Response JSON has `response` and `session_id` with matching session. |
| `test_response_is_non_empty` | LLM returns a non-empty answer. |
| `test_open_chat_context_persists_across_turns` | A follow-up question on the same session returns a valid response. |

#### `TestExtractProfile` (2 tests)

Covers the profile extraction endpoint (`/api/chat/extract-profile`).

| Test | What it checks |
|---|---|
| `test_no_conversation_returns_404` | Extracting from a session with no prior messages returns 404. |
| `test_extract_after_conversation` | After 3 messages, the endpoint returns 200 with a `profile` dict and the correct `session_id`. |

---

## `application_tracking/` — Application Lifecycle Tests

This sub-suite tests the end-to-end journey of a financial product application: creation, retrieval, status transitions, and status history integrity. It uses a local `created_application` fixture that pre-creates an application so individual tests don't repeat setup.

---

### `application_tracking/test_applications.py`

**Endpoints:** `POST /api/applications`, `GET /api/applications/{session_id}`, `PATCH /api/applications/{application_id}`  
**Tests:** 21

#### Local fixture: `created_application`

Creates a fresh `ins-001` application before each test that requests it. Returns a tuple of `(session_id, application_id, application_dict)` so individual tests can reference all three without making their own POST.

#### `TestCreateApplication` (9 tests)

| Test | What it checks |
|---|---|
| `test_create_returns_200` | POST returns HTTP 200. |
| `test_response_has_application_key` | Response JSON contains an `application` key. |
| `test_application_fields_present` | All 10 required fields are present on the created document. |
| `test_initial_status_is_submitted` | Freshly created application always starts at `status: "submitted"`. |
| `test_application_id_has_app_prefix` | `application_id` starts with `"APP-"`. |
| `test_policy_metadata_copied_to_application` | `policy_name` and `category` are copied from the matched policy at creation time. |
| `test_user_profile_stored_correctly` | `user_profile.name` and `user_profile.monthly_salary` match the submitted payload. |
| `test_invalid_policy_returns_404` | Submitting a non-existent `policy_id` returns 404. |
| `test_can_apply_to_each_category` | Parametrized — one application per category (`ins`, `loan`, `cc`, `inv`, `ba`) all return 200. |

#### `TestGetApplications` (6 tests)

| Test | What it checks |
|---|---|
| `test_get_returns_200` | GET by session ID returns 200. |
| `test_response_shape` | Response has `applications` list and `count` integer. |
| `test_created_application_appears_in_list` | The application created by the fixture appears in the session's list. |
| `test_multiple_applications_for_same_session` | Creating 2 applications under one session returns `count: 2`. |
| `test_empty_session_returns_zero_count` | A never-used session ID returns `count: 0` and an empty list. |
| `test_sessions_are_isolated` | An application created for session A does not appear in session B's results. |

#### `TestUpdateApplicationStatus` (6 tests)

| Test | What it checks |
|---|---|
| `test_update_status_returns_200` | PATCH returns 200. |
| `test_status_reflects_update` | After a PATCH, the returned `status` matches the requested value. |
| `test_status_history_grows_on_each_update` | After two updates, `status_history` has at least 3 entries (1 create + 2 updates). |
| `test_status_history_entry_has_required_fields` | Each history entry contains `status`, `timestamp`, and `note`. |
| `test_first_history_entry_is_submitted` | The first history entry is always `"submitted"`, never an updated value. |
| `test_update_nonexistent_application_returns_404` | PATCHing an unknown `application_id` returns 404. |
| `test_all_standard_statuses_accepted` | Parametrized across `submitted`, `under_review`, `approved`, `rejected`, `withdrawn` — all are accepted and reflected back. |

---

## `db/` — Schema and Data Validation Tests

This sub-suite validates the data contracts that the API produces and consumes. It does not test business logic — it tests that every object in the system is well-typed, correctly formatted, and internally consistent. Think of it as a runtime schema enforcement layer.

---

### `db/test_user_schema.py`

**Tests:** 30

Contains five test classes, each focused on a different entity or concern.

#### `TestPolicySchema` (13 tests)

Iterates over every policy returned by `GET /api/policies` and asserts type and format invariants.

| Test | What it checks |
|---|---|
| `test_policy_id_is_nonempty_string` | `policy_id` is a non-empty string on every policy. |
| `test_policy_ids_are_unique` | No two policies share the same `policy_id`. |
| `test_policy_id_format` | `policy_id` matches the regex `^[a-z_]+-\d{3}$` (e.g. `ins-001`, `ba-002`). |
| `test_category_is_valid_enum` | `category` is one of `insurance`, `loan`, `credit_card`, `investment`, `bank_account`. |
| `test_risk_level_is_valid_enum` | `risk_level` is one of `low`, `medium`, `high`. |
| `test_sharia_compliant_is_boolean` | `sharia_compliant` is a Python `bool`, not a string or integer. |
| `test_min_salary_is_non_negative_int` | `min_salary` is a non-negative integer. |
| `test_age_bounds_are_valid` | `min_age > 0` and `min_age < max_age` on every policy. |
| `test_rating_is_between_0_and_5` | `rating` is a number in the range `[0, 5]`. |
| `test_name_and_provider_are_nonempty_strings` | Both `name` and `provider` are non-empty strings. |
| `test_benefits_is_list_of_strings` | `benefits` is a list and every element is a string. |
| `test_features_is_dict` | `features` is a dictionary. |
| `test_sharia_policies_are_subset_of_all` | Sharia-compliant policies form a proper subset of all policies, and at least one exists. |

#### `TestNewsSchema` (4 tests)

Validates the news article objects from `GET /api/news`.

| Test | What it checks |
|---|---|
| `test_news_ids_are_unique` | All `news_id` values are unique. |
| `test_date_format_is_iso` | `date` matches `YYYY-MM-DD` format on every article. |
| `test_title_and_summary_are_nonempty` | Neither `title` nor `summary` is blank or whitespace-only. |
| `test_source_is_nonempty_string` | `source` is a non-empty string. |

#### `TestUserProfileSchema` (6 tests)

Builds a real profile by sending 4 messages to the avatar chat and calling `extract-profile`, then validates the returned object. Because this relies on the LLM, the assertions are type-level rather than value-level.

| Test | What it checks |
|---|---|
| `test_extract_returns_all_expected_keys` | Profile contains all 11 expected keys (`name`, `age`, `nationality`, `residency_status`, `monthly_salary`, `employment_type`, `financial_goal`, `risk_appetite`, `sharia_compliant`, `specific_requirements`, `completeness_score`). |
| `test_completeness_score_in_range` | `completeness_score` is a number between 0 and 100. |
| `test_rich_conversation_yields_high_completeness` | After 4 informative messages the score is ≥ 40. |
| `test_sharia_compliant_is_bool_or_none` | `sharia_compliant` is either a boolean or `null`. |
| `test_monthly_salary_is_numeric_or_none` | `monthly_salary` is either a number or `null`. |
| `test_age_is_positive_int_or_none` | `age` is either a positive integer or `null`. |

#### `TestApplicationSchema` (9 tests)

Creates applications and validates the schema of both individual and listed responses.

| Test | What it checks |
|---|---|
| `test_all_required_fields_present` | All 10 required fields are present on a new application. |
| `test_application_id_uppercase_hex` | `application_id` matches `^APP-[A-F0-9]{8}$`. |
| `test_category_matches_policy` | Applying for `loan-001` yields `category: "loan"` on the application. |
| `test_created_at_is_iso_datetime` | `created_at` is an ISO 8601 datetime string with timezone info (`T` and `Z` or `+`). |
| `test_status_history_has_one_entry_on_create` | A brand new application has exactly 1 history entry. |
| `test_status_history_entry_shape` | Each history entry has `status`, `timestamp`, and `note`. |
| `test_status_history_timestamp_is_iso` | History entry `timestamp` contains a `T` separator (ISO 8601). |
| `test_user_profile_stored_as_dict` | `user_profile` is stored as a dictionary, not a string. |
| `test_applications_list_schema` | The list endpoint returns `applications` as a list and `count` as an int; each item passes the field check. |

#### `TestStoreConsistency` (5 tests)

Cross-entity referential integrity checks — confirms the in-memory store is internally consistent.

| Test | What it checks |
|---|---|
| `test_all_policy_ids_are_retrievable` | Every ID in `known_policy_ids` can be fetched individually from `GET /api/policies/{id}`. |
| `test_application_policy_id_references_valid_policy` | After creating an application, its `policy_id` field resolves to a real policy via `GET /api/policies/{id}`. |
| `test_count_field_matches_list_length_for_policies` | `count` equals `len(policies)` on the policies list response. |
| `test_count_field_matches_list_length_for_news` | `count` equals `len(news)` on the news list response. |
| `test_count_field_matches_list_length_for_applications` | After creating 3 applications for one session, `count` equals `len(applications)` in the response. |

---

## Test Count Summary

| Sub-suite | File | Tests |
|---|---|---|
| API | `api/test_health.py` | 3 |
| API | `api/test_policies.py` | 25 |
| API | `api/test_news.py` | 9 |
| API | `api/test_chat.py` | 11 |
| Application Tracking | `application_tracking/test_applications.py` | 21 |
| Schema / DB | `db/test_user_schema.py` | 30 |
| **Total** | | **99** |

---

## Key Design Decisions

**No mocks.** Every test hits the real backend. This means a passing suite guarantees the actual HTTP contract works, not just that internal functions return the right values.

**Session isolation.** Every test that touches stateful endpoints generates a UUID-based session ID. This prevents test ordering from affecting results and allows the full suite to run in parallel safely.

**Parametrized breadth tests.** Category filters, risk levels, product categories, and application statuses are all tested via `@pytest.mark.parametrize` rather than duplicated test functions. Adding a new enum value to the schema means adding it to one list in the test file.

**Schema tests are type-level, not value-level.** The `db/` suite does not assert that a specific policy has a specific name — the `api/` suite does that where needed. The `db/` suite only cares that types are correct, IDs are unique, and formats match — invariants that should hold across any future seed data change.

**LLM-dependent tests use loose assertions.** Tests that call the chat endpoints and extract profiles cannot assert exact LLM output, so they assert structural properties: non-empty strings, correct keys, numeric ranges. This makes the suite stable across model changes.

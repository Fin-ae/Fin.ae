import pytest
from server import normalize_policy_category, infer_category_from_policy_id

def test_normalize_policy_category():
    assert normalize_policy_category("credit card") == "credit_card"
    assert normalize_policy_category("loans") == "loan"
    assert normalize_policy_category("bank account") == "bank_account"
    assert normalize_policy_category("investments") == "investment"
    assert normalize_policy_category(None) is None

def test_infer_category_from_policy_id():
    assert infer_category_from_policy_id("ins-123") == "insurance"
    assert infer_category_from_policy_id("loan-abc") == "loan"
    assert infer_category_from_policy_id("cc-test") == "credit_card"
    assert infer_category_from_policy_id("inv-001") == "investment"
    assert infer_category_from_policy_id("ba-123") == "bank_account"
    assert infer_category_from_policy_id("unknown-123") is None

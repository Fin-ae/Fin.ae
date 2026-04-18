from loan_scraper import extract_interest_rate, extract_tenure, extract_salary, build_row


# -----------------------------
# TEST 1: Interest Rate
# -----------------------------
def test_interest_rate():
    text = "Loan interest starts from 5.99% per annum"
    assert extract_interest_rate(text) == 5.99


# -----------------------------
# TEST 2: Tenure in months
# -----------------------------
def test_tenure_months():
    text = "Repayment period up to 48 months"
    assert extract_tenure(text) == 48


# -----------------------------
# TEST 3: Tenure in years
# -----------------------------
def test_tenure_years():
    text = "Loan tenure is up to 4 years"
    assert extract_tenure(text) == 48


# -----------------------------
# TEST 4: Salary extraction
# -----------------------------
def test_salary():
    text = "Minimum salary required AED 5000"
    assert extract_salary(text) == 5000


# -----------------------------
# TEST 5: build_row fallback logic
# -----------------------------
def test_build_row_fallback():
    bank = {
        "bank": "ADCB",
        "rate": 7.25,
        "tenure": 48,
        "salary": 5000
    }

    row = build_row(
        bank,
        "https://example.com",
        None,     # scraped rate missing
        None,     # scraped tenure missing
        None,     # scraped salary missing
        "page_accessed"
    )

    assert row["final_interest_rate"] == 7.25
    assert row["final_tenure_months"] == 48
    assert row["final_minimum_salary_aed"] == 5000
    assert row["data_quality"] == "partial_scrape_manual_values_used"
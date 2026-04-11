"""
Step 2: Scraping
- Build scraper
- Extract data

"""

import requests
import time
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from step1_sources import BANKS, PRODUCTS, FIELDS

# ── Utility ───────────────────────────────────────────────────────────────────

def mock_fetch(bank: dict, product_type: str) -> list[dict]:
    """
    Simulates what a real scraper would extract from a bank product page.
    Replace this function body with actual requests + BeautifulSoup parsing.

    Real implementation would look like:
        url = f"{bank['url']}/personal/{product_type.replace('_','-')}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        # parse rate, balance, fees from soup...
    """
    time.sleep(0.05)  # simulate network latency

    product_templates = {
        "savings_account": [
            {"product_name": "Smart Saver",        "interest_rate_pct": 2.75, "min_balance_aed": 3000,  "max_balance_aed": None,   "currency": "AED", "tenure_months": 0,  "fees_aed": 0,   "eligibility": "UAE Resident"},
            {"product_name": "eSaver Account",     "interest_rate_pct": 3.10, "min_balance_aed": 1000,  "max_balance_aed": None,   "currency": "AED", "tenure_months": 0,  "fees_aed": 0,   "eligibility": "UAE Resident"},
        ],
        "current_account": [
            {"product_name": "Business Current",   "interest_rate_pct": 0.0,  "min_balance_aed": 10000, "max_balance_aed": None,   "currency": "AED", "tenure_months": 0,  "fees_aed": 25,  "eligibility": "UAE Resident"},
            {"product_name": "Personal Current",   "interest_rate_pct": 0.0,  "min_balance_aed": 3000,  "max_balance_aed": None,   "currency": "AED", "tenure_months": 0,  "fees_aed": 0,   "eligibility": "UAE Resident"},
        ],
        "fixed_deposit": [
            {"product_name": "3-Month FD",         "interest_rate_pct": 4.50, "min_balance_aed": 10000, "max_balance_aed": None,   "currency": "AED", "tenure_months": 3,  "fees_aed": 0,   "eligibility": "UAE Resident"},
            {"product_name": "12-Month FD",        "interest_rate_pct": 5.20, "min_balance_aed": 10000, "max_balance_aed": None,   "currency": "AED", "tenure_months": 12, "fees_aed": 0,   "eligibility": "UAE Resident"},
            {"product_name": "6-Month FD",         "interest_rate_pct": 4.85, "min_balance_aed": 5000,  "max_balance_aed": None,   "currency": "AED", "tenure_months": 6,  "fees_aed": 0,   "eligibility": "UAE Resident"},
        ],
        "personal_loan": [
            {"product_name": "Salary Transfer Loan","interest_rate_pct": 6.99, "min_balance_aed": 0,    "max_balance_aed": 500000, "currency": "AED", "tenure_months": 48, "fees_aed": 1000,"eligibility": "Salary Transfer"},
            {"product_name": "Non-Salary Loan",    "interest_rate_pct": 8.99, "min_balance_aed": 0,    "max_balance_aed": 250000, "currency": "AED", "tenure_months": 36, "fees_aed": 1500,"eligibility": "UAE Resident"},
        ],
        "credit_card": [
            {"product_name": "Cashback Platinum",  "interest_rate_pct": 36.0, "min_balance_aed": 0,    "max_balance_aed": None,   "currency": "AED", "tenure_months": 0,  "fees_aed": 800, "eligibility": "Min salary AED 5,000"},
            {"product_name": "Travel Miles Card",  "interest_rate_pct": 36.0, "min_balance_aed": 0,    "max_balance_aed": None,   "currency": "AED", "tenure_months": 0,  "fees_aed": 1200,"eligibility": "Min salary AED 8,000"},
        ],
        "mortgage": [
            {"product_name": "Fixed Rate Mortgage","interest_rate_pct": 4.25, "min_balance_aed": 0,    "max_balance_aed": 5000000,"currency": "AED", "tenure_months": 300,"fees_aed": 0,   "eligibility": "UAE Resident"},
            {"product_name": "Variable Mortgage",  "interest_rate_pct": 3.99, "min_balance_aed": 0,    "max_balance_aed": 5000000,"currency": "AED", "tenure_months": 300,"fees_aed": 0,   "eligibility": "UAE Resident"},
        ],
    }

    templates = product_templates.get(product_type, [])
    results = []
    for t in templates:
        # Add slight variance per bank to simulate real different rates
        variance = round(random.uniform(-0.3, 0.3), 2)
        record = {
            **t,
            "bank_name":    bank["name"],
            "product_type": product_type,
            "interest_rate_pct": max(0, round(t["interest_rate_pct"] + variance, 2)),
            "source_url":   f"{bank['url']}/personal/{product_type.replace('_','-')}",
            "scraped_at":   datetime.now(timezone.utc).isoformat(),
        }
        results.append(record)
    return results


def scrape_all() -> list[dict]:
    all_records = []
    total = len(BANKS) * len(PRODUCTS)
    done = 0

    print(f"Starting scrape: {len(BANKS)} banks × {len(PRODUCTS)} products = {total} requests\n")

    for bank in BANKS:
        for product_type in PRODUCTS:
            try:
                records = mock_fetch(bank, product_type)
                all_records.extend(records)
                done += 1
                print(f"  [{done:>2}/{total}] {bank['name']:<20} {product_type:<20} → {len(records)} records")
            except Exception as e:
                print(f"  ERROR {bank['name']} / {product_type}: {e}")

    print(f"\nTotal records extracted: {len(all_records)}")
    return all_records


if __name__ == "__main__":
    data = scrape_all()

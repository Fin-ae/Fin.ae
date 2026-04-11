"""
=============================================================================
STEP 2: SCRAPING
=============================================================================
PURPOSE:
    This file is responsible for fetching raw product data from each bank's
    website and returning it as a list of dictionaries that match the schema
    defined in step1_sources.py.

WHY SCRAPING IS NEEDED:
    Banks do not provide a public API for their product rates and terms. The
    only way to collect this data at scale is to visit each bank's product
    pages and extract the relevant figures (rates, fees, balances) from the
    HTML content — this is called web scraping.

ARCHITECTURE CHOICE — mock_fetch() vs real HTTP:
    Real bank websites often use JavaScript to render content dynamically,
    which means a plain HTTP request won't return the product data. They may
    also require session cookies or rate-limit automated requests.
    
    To keep this code runnable without a live browser environment, we use
    mock_fetch() which returns realistic simulated data. The function is
    structured identically to how a real scraper would work — just swap the
    body with actual requests + BeautifulSoup (or Selenium) calls to go live.
=============================================================================
"""

import requests          # Used for making real HTTP GET requests to bank URLs
import time              # Used to add delays between requests (rate limiting)
import random            # Used in mock mode to simulate per-bank rate variance
from datetime import datetime, timezone  # For timestamping each scraped record
from bs4 import BeautifulSoup            # HTML parser for extracting data from pages
from step1_sources import BANKS, PRODUCTS, FIELDS  # Central config from step 1

# =============================================================================
# HTTP HEADERS
# =============================================================================
# WHY: When making real HTTP requests, we set a User-Agent header so the
# server identifies the request as coming from a browser. Without this, many
# websites return a 403 Forbidden error or serve a bot-detection page instead
# of the actual product content.
# =============================================================================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# =============================================================================
# mock_fetch()
# =============================================================================
# WHY THIS EXISTS:
#   Real bank websites render product data with JavaScript frameworks, making
#   them hard to scrape without a headless browser (e.g. Selenium/Playwright).
#   This mock simulates the output of a real scraper so the rest of the
#   pipeline (cleaning, exporting) can be developed and tested independently.
#
# HOW TO REPLACE WITH REAL SCRAPING:
#   When you are ready to scrape live data, replace the body of this function
#   with something like:
#
#       url = f"{bank['url']}/personal/{product_type.replace('_', '-')}"
#       resp = requests.get(url, headers=HEADERS, timeout=15)
#       soup = BeautifulSoup(resp.text, "html.parser")
#       rate = soup.select_one(".interest-rate").text.strip()
#       ...
#
#   For JavaScript-heavy pages, use Selenium or Playwright instead:
#       from selenium import webdriver
#       driver = webdriver.Chrome()
#       driver.get(url)
#       rate = driver.find_element(By.CLASS_NAME, "rate-value").text
# =============================================================================
def mock_fetch(bank: dict, product_type: str) -> list[dict]:
    """
    Simulates scraping a bank's product page.
    Returns a list of product records matching the FIELDS schema.
    """

    # WHY time.sleep: In real scraping we add a delay between requests to
    # avoid overwhelming the bank's server and to reduce the risk of being
    # blocked by rate-limiting or bot detection systems.
    time.sleep(0.05)

    # WHY product_templates: Each product type has a different set of typical
    # products (e.g. a bank might offer both a 3-month and 12-month FD). This
    # dictionary defines representative template records for each product type,
    # mirroring what would realistically be found on a bank's product page.
    product_templates = {
        "savings_account": [
            {
                "product_name":      "Smart Saver",
                "interest_rate_pct": 2.75,
                "min_balance_aed":   3000,
                "max_balance_aed":   None,   # None = no upper limit
                "currency":          "AED",
                "tenure_months":     0,      # 0 = no fixed term
                "fees_aed":          0,
                "eligibility":       "UAE Resident",
            },
            {
                "product_name":      "eSaver Account",
                "interest_rate_pct": 3.10,
                "min_balance_aed":   1000,
                "max_balance_aed":   None,
                "currency":          "AED",
                "tenure_months":     0,
                "fees_aed":          0,
                "eligibility":       "UAE Resident",
            },
        ],
        "current_account": [
            {
                "product_name":      "Business Current",
                "interest_rate_pct": 0.0,    # Current accounts typically earn no interest
                "min_balance_aed":   10000,
                "max_balance_aed":   None,
                "currency":          "AED",
                "tenure_months":     0,
                "fees_aed":          25,     # Monthly maintenance fee
                "eligibility":       "UAE Resident",
            },
            {
                "product_name":      "Personal Current",
                "interest_rate_pct": 0.0,
                "min_balance_aed":   3000,
                "max_balance_aed":   None,
                "currency":          "AED",
                "tenure_months":     0,
                "fees_aed":          0,
                "eligibility":       "UAE Resident",
            },
        ],
        "fixed_deposit": [
            # WHY three tenures: FDs are offered at multiple tenures because
            # longer lock-in periods earn higher interest rates.
            {
                "product_name":      "3-Month FD",
                "interest_rate_pct": 4.50,
                "min_balance_aed":   10000,
                "max_balance_aed":   None,
                "currency":          "AED",
                "tenure_months":     3,
                "fees_aed":          0,
                "eligibility":       "UAE Resident",
            },
            {
                "product_name":      "6-Month FD",
                "interest_rate_pct": 4.85,
                "min_balance_aed":   5000,
                "max_balance_aed":   None,
                "currency":          "AED",
                "tenure_months":     6,
                "fees_aed":          0,
                "eligibility":       "UAE Resident",
            },
            {
                "product_name":      "12-Month FD",
                "interest_rate_pct": 5.20,
                "min_balance_aed":   10000,
                "max_balance_aed":   None,
                "currency":          "AED",
                "tenure_months":     12,
                "fees_aed":          0,
                "eligibility":       "UAE Resident",
            },
        ],
        "personal_loan": [
            {
                "product_name":      "Salary Transfer Loan",
                "interest_rate_pct": 6.99,
                "min_balance_aed":   0,
                "max_balance_aed":   500000,  # Maximum loan amount
                "currency":          "AED",
                "tenure_months":     48,
                "fees_aed":          1000,    # Processing / arrangement fee
                "eligibility":       "Salary Transfer",
            },
            {
                "product_name":      "Non-Salary Loan",
                "interest_rate_pct": 8.99,   # Higher rate = higher risk for bank
                "min_balance_aed":   0,
                "max_balance_aed":   250000,
                "currency":          "AED",
                "tenure_months":     36,
                "fees_aed":          1500,
                "eligibility":       "UAE Resident",
            },
        ],
        "credit_card": [
            {
                "product_name":      "Cashback Platinum",
                "interest_rate_pct": 36.0,   # Annual purchase rate (APR)
                "min_balance_aed":   0,
                "max_balance_aed":   None,
                "currency":          "AED",
                "tenure_months":     0,
                "fees_aed":          800,    # Annual card fee
                "eligibility":       "Min salary AED 5,000",
            },
            {
                "product_name":      "Travel Miles Card",
                "interest_rate_pct": 36.0,
                "min_balance_aed":   0,
                "max_balance_aed":   None,
                "currency":          "AED",
                "tenure_months":     0,
                "fees_aed":          1200,
                "eligibility":       "Min salary AED 8,000",
            },
        ],
        "mortgage": [
            {
                "product_name":      "Fixed Rate Mortgage",
                "interest_rate_pct": 4.25,
                "min_balance_aed":   0,
                "max_balance_aed":   5000000,
                "currency":          "AED",
                "tenure_months":     300,    # 25-year mortgage term
                "fees_aed":          0,
                "eligibility":       "UAE Resident",
            },
            {
                "product_name":      "Variable Mortgage",
                "interest_rate_pct": 3.99,   # Lower initial rate but can change
                "min_balance_aed":   0,
                "max_balance_aed":   5000000,
                "currency":          "AED",
                "tenure_months":     300,
                "fees_aed":          0,
                "eligibility":       "UAE Resident",
            },
        ],
    }

    templates = product_templates.get(product_type, [])
    results = []

    for t in templates:
        # WHY variance: Different banks genuinely offer slightly different rates
        # for the same product type. Adding a small random variance simulates
        # the real-world variation we would find when scraping multiple banks.
        variance = round(random.uniform(-0.3, 0.3), 2)

        record = {
            **t,  # Spread all template fields into the record
            "bank_name":         bank["name"],
            "product_type":      product_type,
            # max() ensures rate never goes negative due to variance
            "interest_rate_pct": max(0, round(t["interest_rate_pct"] + variance, 2)),
            # source_url records exactly which page this data came from
            "source_url":        f"{bank['url']}/personal/{product_type.replace('_', '-')}",
            # scraped_at uses UTC to avoid timezone ambiguity across servers
            "scraped_at":        datetime.now(timezone.utc).isoformat(),
        }
        results.append(record)

    return results


# =============================================================================
# scrape_all()
# =============================================================================
# WHY: This is the orchestration function that loops over every combination of
# bank × product_type and calls mock_fetch() for each pair. It collects all
# results into a single flat list that gets passed to step 3 for cleaning.
#
# WHY try/except per request: If one bank's page fails (network error, changed
# HTML structure, rate limit), we log the error and continue rather than
# crashing the entire pipeline. This makes the scraper resilient to partial
# failures — we still get data from all the banks that succeeded.
# =============================================================================
def scrape_all() -> list[dict]:
    """
    Iterates over all bank × product combinations and collects raw records.
    Returns a flat list of all extracted product dictionaries.
    """
    all_records = []
    total = len(BANKS) * len(PRODUCTS)
    done = 0

    print(f"Starting scrape: {len(BANKS)} banks × {len(PRODUCTS)} products = {total} requests\n")

    for bank in BANKS:
        for product_type in PRODUCTS:
            try:
                records = mock_fetch(bank, product_type)
                all_records.extend(records)   # extend = add all items from list
                done += 1
                print(f"  [{done:>2}/{total}] {bank['name']:<20} {product_type:<20} → {len(records)} records")
            except Exception as e:
                # WHY we catch broadly: Network errors, parsing errors, and
                # unexpected page structures should not halt the whole run.
                print(f"  ERROR  {bank['name']} / {product_type}: {e}")

    print(f"\nTotal records extracted: {len(all_records)}")
    return all_records


# =============================================================================
# SELF-TEST
# =============================================================================
# WHY: Running this file directly lets a developer verify the scraper works
# end-to-end and see sample output before integrating into the full pipeline.
# =============================================================================
if __name__ == "__main__":
    data = scrape_all()
    print(f"\nSample record:\n{data[0]}")

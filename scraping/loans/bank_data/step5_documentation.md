# Bank Product Data Pipeline — Process Documentation

## Overview

This pipeline collects, cleans, and exports banking product data (interest rates, minimum balances, fees) from UAE retail banks into structured JSON and CSV files for downstream consumption by the AI product recommendation assistant.

---

## Pipeline Architecture

```
step1_sources.py  →  step2_scraper.py  →  step3_cleaning.py  →  step4_output.py
  Define banks          Extract raw           Standardize &         Write JSON/CSV
  & fields              product data          deduplicate           to /scraping/accounts/
```

---

## Steps

### Step 1: Identify Sources (`step1_sources.py`)

Defines the list of target banks and the canonical field schema every product record must conform to.

**Banks covered:** HSBC UAE, Emirates NBD, FAB, ADCB, Mashreq, DIB, RAKBank, CBD

**Product types:** savings_account, current_account, fixed_deposit, personal_loan, credit_card, mortgage

**Fields per record:**

| Field | Type | Description |
|---|---|---|
| `bank_name` | string | Bank name, e.g. "Emirates NBD" |
| `product_type` | string | Product category slug |
| `product_name` | string | Specific product name |
| `interest_rate_pct` | float | Annual interest/profit rate (%) |
| `min_balance_aed` | float | Minimum balance in AED |
| `max_balance_aed` | float or null | Maximum balance (null = unlimited) |
| `currency` | string | ISO currency code (default: AED) |
| `tenure_months` | int | Tenure in months (0 = no fixed tenure) |
| `fees_aed` | float | Annual/monthly fee in AED |
| `eligibility` | string | Eligibility criteria |
| `source_url` | string | Scraped page URL |
| `scraped_at` | string | ISO 8601 UTC timestamp |

---

### Step 2: Scraping (`step2_scraper.py`)

Fetches product data from each bank's website.

**Architecture:**
- `mock_fetch(bank, product_type)` — the extraction unit. Replace the mock body with real HTTP requests and BeautifulSoup parsing to go live.
- `scrape_all()` — iterates over all bank × product combinations, collects records.

**To go live with real scraping:**
```python
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 ..."}

def real_fetch(bank, product_type):
    url = f"{bank['url']}/personal/{product_type.replace('_', '-')}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    # Parse rate from e.g. soup.select_one(".rate-value").text
    # ...
```

> **Note:** For JavaScript-rendered pages, use `selenium` or `playwright` instead of `requests`.

---

### Step 3: Cleaning (`step3_cleaning.py`)

**Standardize formats:**
- String fields: stripped, title-cased
- `product_type`: lowercased, underscored
- `currency`: uppercased
- Numeric fields: coerced to float, NaN → 0
- Timestamps: normalized to ISO 8601 UTC

**Remove duplicates:**
- Dedup key: `bank_name + product_type + product_name + interest_rate_pct`
- Strategy: keep most recently scraped record

**Data quality flags:**
- `suspect_rate` — interest rate > 50%
- `negative_balance` — min_balance < 0
- `missing_name` — product name < 2 characters

---

### Step 4: Output (`step4_output.py`)

Writes three sets of files to `/scraping/accounts/`:

1. `bank_products_<timestamp>.csv` — full dataset in CSV
2. `bank_products_<timestamp>.json` — full dataset in JSON with metadata wrapper
3. `<product_type>.csv` per product type — e.g. `fixed_deposit.csv`, `credit_card.csv`

**JSON structure:**
```json
{
  "metadata": {
    "generated_at": "2025-04-11T...",
    "total_records": 96,
    "banks": ["ADCB", "CBD", ...],
    "product_types": ["credit_card", "fixed_deposit", ...],
    "schema_version": "1.0"
  },
  "data": [ { ...record... }, ... ]
}
```

---

### Step 5: Documentation (`step5_documentation.md`)

This file. Keep it updated whenever the schema, banks list, or cleaning rules change.

---

## Running the Full Pipeline

```bash
cd scraping/
python run_pipeline.py
```

Output files will appear in `/scraping/accounts/`.

---

## Maintenance Notes

- **Adding a bank:** Add an entry to `BANKS` in `step1_sources.py`, then add product templates in `step2_scraper.py > mock_fetch()`.
- **Adding a field:** Add to `FIELDS` in `step1_sources.py`, update `mock_fetch()`, and update `standardize_formats()` in `step3_cleaning.py`.
- **Scheduling:** Run via cron or a task scheduler weekly to keep rates current.
- **Rate changes:** Interest rates change frequently. Always timestamp records and treat data older than 7 days as potentially stale.

---

## Compliance

- Always check `robots.txt` before scraping any bank website
- Do not store personally identifiable information (PII)
- This data is for informational/educational use — not for automated financial advice
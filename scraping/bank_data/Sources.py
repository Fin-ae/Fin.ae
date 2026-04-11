"""
Step 1: Identify Sources
- List banks and products
- Define fields (interest rate, minimum balance)
"""

BANKS = [
    {"name": "HSBC UAE",         "url": "https://www.hsbc.ae"},
    {"name": "Emirates NBD",     "url": "https://www.emiratesnbd.com"},
    {"name": "FAB",              "url": "https://www.bankfab.com"},
    {"name": "ADCB",             "url": "https://www.adcb.com"},
    {"name": "Mashreq",          "url": "https://www.mashreq.com"},
    {"name": "DIB",              "url": "https://www.dib.ae"},
    {"name": "RAKBank",          "url": "https://www.rakbank.ae"},
    {"name": "CBD",              "url": "https://www.cbd.ae"},
]

PRODUCTS = [
    "savings_account",
    "current_account",
    "fixed_deposit",
    "personal_loan",
    "credit_card",
    "mortgage",
]

# Canonical field schema — every product record must have these keys
FIELDS = {
    "bank_name":         str,    # e.g. "Emirates NBD"
    "product_type":      str,    # e.g. "savings_account"
    "product_name":      str,    # e.g. "Live Savings Account"
    "interest_rate_pct": float,  # Annual interest / profit rate (%)
    "min_balance_aed":   float,  # Minimum balance in AED
    "max_balance_aed":   float,  # Maximum balance (None if unlimited)
    "currency":          str,    # e.g. "AED", "USD"
    "tenure_months":     int,    # Relevant for FDs and loans
    "fees_aed":          float,  # Monthly/annual fee in AED
    "eligibility":       str,    # e.g. "UAE Resident", "Expat"
    "source_url":        str,    # Page scraped from
    "scraped_at":        str,    # ISO timestamp
}

if __name__ == "__main__":
    print(f"Banks defined   : {len(BANKS)}")
    print(f"Product types   : {len(PRODUCTS)}")
    print(f"Fields per record: {len(FIELDS)}")
    print("\nBanks:")
    for b in BANKS:
        print(f"  - {b['name']}")
    print("\nFields:")
    for f in FIELDS:
        print(f"  - {f}")

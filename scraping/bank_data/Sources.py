"""
=============================================================================
STEP 1: IDENTIFY SOURCES
=============================================================================
PURPOSE:
    This file is the single source of truth for the entire pipeline.
    It defines:
      1. BANKS    — which banks we want to collect product data from
      2. PRODUCTS — which product categories we care about
      3. FIELDS   — the exact data structure (schema) every record must follow

WHY THIS IS DONE AS A SEPARATE FILE:
    Centralising the configuration here means that if we need to add a new
    bank, remove a product type, or add a new field, we only change it in
    one place. All other steps (scraper, cleaner, exporter) import from here,
    so they automatically pick up the changes without needing to be edited.
=============================================================================
"""

# =============================================================================
# BANKS
# =============================================================================
# WHY: We define the list of target banks here so the scraper in step2 can
# loop over them programmatically. Each entry contains:
#   - "name": human-readable display name used in reports and output files
#   - "url":  base URL used to construct product page URLs during scraping
#
# These are the major UAE retail banks chosen because they offer a broad range
# of personal banking products and have publicly accessible product pages.
# =============================================================================
BANKS = [
    {"name": "HSBC UAE",      "url": "https://www.hsbc.ae"},
    {"name": "Emirates NBD",  "url": "https://www.emiratesnbd.com"},
    {"name": "FAB",           "url": "https://www.bankfab.com"},
    {"name": "ADCB",          "url": "https://www.adcb.com"},
    {"name": "Mashreq",       "url": "https://www.mashreq.com"},
    {"name": "DIB",           "url": "https://www.dib.ae"},
    {"name": "RAKBank",       "url": "https://www.rakbank.ae"},
    {"name": "CBD",           "url": "https://www.cbd.ae"},
]

# =============================================================================
# PRODUCTS
# =============================================================================
# WHY: We define the product categories as standardised slugs (lowercase,
# underscored). These slugs are reused in three places:
#   - As URL segments when building scrape URLs (/personal/fixed-deposit)
#   - As the "product_type" field value in every data record
#   - As filenames when exporting per-product CSVs in step 4
#
# We chose these 6 categories because they cover the core retail banking
# products customers compare most: deposit products, borrowing products,
# and everyday payment products.
# =============================================================================
PRODUCTS = [
    "savings_account",   # Interest-bearing accounts for storing money
    "current_account",   # Everyday transactional accounts, usually no interest
    "fixed_deposit",     # Locked-in term deposits offering higher interest rates
    "personal_loan",     # Unsecured cash loans repaid in fixed instalments
    "credit_card",       # Revolving credit lines with reward/cashback features
    "mortgage",          # Secured home purchase or refinance loans
]

# =============================================================================
# FIELDS (Schema Definition)
# =============================================================================
# WHY: This dictionary defines the canonical schema — the agreed set of fields
# that every product record MUST contain. Defining it here serves two purposes:
#
#   1. DOCUMENTATION — anyone reading the code immediately understands the
#      data model without needing to look at actual scraped data.
#
#   2. VALIDATION — the cleaning step (step3) uses these types to know what
#      to cast each field to (str, float, int) during standardisation.
#
# Field-by-field rationale:
#   bank_name         — identifies which institution the product belongs to
#   product_type      — the category slug, links back to the PRODUCTS list above
#   product_name      — the specific product marketing name (e.g. "Live Saver")
#   interest_rate_pct — the headline annual rate shown to customers, as a %
#   min_balance_aed   — minimum amount needed to open or maintain the product
#   max_balance_aed   — upper limit (None = no cap, common for savings accounts)
#   currency          — most UAE products are AED, but some offer USD variants
#   tenure_months     — how long funds are locked in (0 = no fixed term)
#   fees_aed          — annual or monthly fee charged to the customer in AED
#   eligibility       — who can apply (e.g. "UAE Resident", "Salary Transfer")
#   source_url        — the exact page the data came from, kept for auditing
#   scraped_at        — UTC timestamp recording when the data was collected
# =============================================================================
FIELDS = {
    "bank_name":         str,    # e.g. "Emirates NBD"
    "product_type":      str,    # e.g. "savings_account"
    "product_name":      str,    # e.g. "Live Savings Account"
    "interest_rate_pct": float,  # Annual interest / profit rate (%)
    "min_balance_aed":   float,  # Minimum balance required in AED
    "max_balance_aed":   float,  # Maximum balance (None = unlimited)
    "currency":          str,    # ISO currency code, e.g. "AED", "USD"
    "tenure_months":     int,    # Fixed term in months; 0 = no fixed term
    "fees_aed":          float,  # Annual/monthly fee in AED
    "eligibility":       str,    # Who can apply, e.g. "UAE Resident"
    "source_url":        str,    # Scraped page URL — audit trail
    "scraped_at":        str,    # ISO 8601 UTC timestamp of collection
}

# =============================================================================
# SELF-TEST
# =============================================================================
# WHY: The if __name__ == "__main__" block lets us run this file standalone
# (python step1_sources.py) to quickly verify the configuration is correct
# without running the full pipeline. This is a standard Python pattern that
# makes a module both importable by other steps AND independently executable.
# =============================================================================
if __name__ == "__main__":
    print(f"Banks defined    : {len(BANKS)}")
    print(f"Product types    : {len(PRODUCTS)}")
    print(f"Fields per record: {len(FIELDS)}")
    print("\nBanks:")
    for b in BANKS:
        print(f"  - {b['name']:<20}  {b['url']}")
    print("\nProduct types:")
    for p in PRODUCTS:
        print(f"  - {p}")
    print("\nFields:")
    for field, ftype in FIELDS.items():
        print(f"  - {field:<22}  ({ftype.__name__})")

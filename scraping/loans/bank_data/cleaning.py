"""
=============================================================================
STEP 3: CLEANING
=============================================================================
PURPOSE:
    Raw scraped data is messy. Different bank websites format numbers,
    strings, and dates differently. This step transforms the raw list of
    dictionaries into a clean, consistent pandas DataFrame by:
      1. Standardising formats — normalising types, casing, and units
      2. Removing duplicates — keeping only one record per unique product

WHY CLEANING IS NECESSARY:
    Without cleaning, downstream steps would break or produce misleading
    output. For example:
      - "aed" vs "AED" vs "Aed" would appear as three different currencies
      - "2.7500001" from float arithmetic would look like a different rate
        than "2.75" from another bank, creating false duplicates
      - A re-run of the scraper without deduplication would double-count
        every record in the output files
      - Invalid values like negative balances would corrupt analysis

WHY PANDAS:
    pandas DataFrames give us vectorised operations (fast, concise) for
    transforming and filtering thousands of rows at once. They also integrate
    directly with the CSV and JSON export functions used in step 4.
=============================================================================
"""

import re                              # Regular expressions (available if needed for text parsing)
import pandas as pd                    # Core data manipulation library
from datetime import datetime, timezone  # For fallback timestamp generation


# =============================================================================
# standardize_formats()
# =============================================================================
# WHY: Converts the raw list of dicts (from the scraper) into a DataFrame
# and enforces consistent data types and formats across all fields.
# This makes every subsequent operation predictable — we always know that
# interest_rate_pct is a float, currency is uppercase, etc.
# =============================================================================
def standardize_formats(records: list[dict]) -> pd.DataFrame:
    """
    Converts raw records to a DataFrame and normalises all field formats.
    Returns a cleaned DataFrame ready for deduplication.
    """

    # WHY pd.DataFrame(records): Converting the list of dicts to a DataFrame
    # at the start lets us use pandas' fast column-wise operations instead of
    # looping through each record manually with a for loop.
    df = pd.DataFrame(records)

    # ── String fields ─────────────────────────────────────────────────────────
    # WHY: String data scraped from web pages often has leading/trailing spaces
    # or inconsistent capitalisation. We normalise them so that "hsbc UAE " and
    # "HSBC UAE" are treated as the same bank during deduplication.
    str_cols = ["bank_name", "product_name", "product_type", "currency", "eligibility"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()  # Remove surrounding whitespace

    df["bank_name"]    = df["bank_name"].str.title()            # "hsbc uae" → "Hsbc Uae"
    df["product_name"] = df["product_name"].str.strip()          # Extra safety strip
    df["product_type"] = df["product_type"].str.lower().str.replace(" ", "_")  # Enforce slug format
    df["currency"]     = df["currency"].str.upper().str.strip()  # "aed" → "AED"

    # ── Numeric fields ────────────────────────────────────────────────────────
    # WHY pd.to_numeric with errors="coerce": If a scraped value is a string
    # like "3.5%" or "N/A", coerce converts it to NaN instead of raising an
    # exception. We then fill NaN with 0.0 as a safe default so downstream
    # calculations don't fail on missing values.
    num_cols = ["interest_rate_pct", "min_balance_aed", "fees_aed", "tenure_months"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # WHY max_balance_aed is handled separately:
    # A None value here means "no upper limit" (e.g. a savings account with no
    # cap). We want to preserve None/NaN rather than replacing it with 0.0,
    # because 0.0 would incorrectly mean "maximum balance is zero".
    if "max_balance_aed" in df.columns:
        df["max_balance_aed"] = pd.to_numeric(df["max_balance_aed"], errors="coerce")
        # NaN is kept intentionally here — do NOT fillna(0)

    # ── Rounding ──────────────────────────────────────────────────────────────
    # WHY round: Floating point arithmetic can produce values like 2.7500000001.
    # Rounding to 2 decimal places ensures rates display cleanly and prevents
    # false duplicates where 2.75 and 2.7500000001 are treated as different rates.
    df["interest_rate_pct"] = df["interest_rate_pct"].round(2)
    df["min_balance_aed"]   = df["min_balance_aed"].round(2)
    df["fees_aed"]          = df["fees_aed"].round(2)
    df["tenure_months"]     = df["tenure_months"].astype(int)  # Must be whole months

    # ── Timestamps ────────────────────────────────────────────────────────────
    # WHY normalise timestamps: The scraper writes ISO 8601 strings, but format
    # can vary slightly (e.g. with/without microseconds). We normalise to a
    # consistent format so sorting by scraped_at in deduplication works correctly.
    def normalize_ts(ts):
        try:
            return pd.to_datetime(ts, utc=True).isoformat()
        except Exception:
            # WHY fallback: If timestamp is missing or malformed, use current
            # UTC time so the record isn't dropped — it just gets a fresh stamp.
            return datetime.now(timezone.utc).isoformat()

    df["scraped_at"] = df["scraped_at"].apply(normalize_ts)

    # ── Data quality flags ────────────────────────────────────────────────────
    # WHY: Rather than silently dropping suspicious records, we flag them with
    # a reason. This lets downstream users decide what to do — they can filter
    # out "suspect_rate" records or investigate them manually.
    df["data_quality"] = "ok"
    df.loc[df["interest_rate_pct"] > 50,       "data_quality"] = "suspect_rate"
    # > 50% APR could indicate a data parsing error (e.g. scraped "50.5%" as "505")
    df.loc[df["min_balance_aed"] < 0,           "data_quality"] = "negative_balance"
    # Negative balance makes no real-world sense — likely a scraping error
    df.loc[df["product_name"].str.len() < 2,    "data_quality"] = "missing_name"
    # A product name under 2 characters means the scraper likely got an empty field

    print(f"  Standardized {len(df)} records")
    return df


# =============================================================================
# remove_duplicates()
# =============================================================================
# WHY: The same product can appear twice if the scraper is run multiple times,
# or if the same product is listed on more than one page of a bank's website.
# Keeping duplicates would inflate record counts and distort comparisons.
#
# DEDUPLICATION STRATEGY:
#   A record is a duplicate if it has the same:
#     bank_name + product_type + product_name + interest_rate_pct
#   We sort by scraped_at descending first so that drop_duplicates(keep="first")
#   retains the MOST RECENTLY scraped version — this ensures we always have
#   the latest rate data when the pipeline is re-run.
# =============================================================================
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes duplicate product records.
    Keeps the most recently scraped version of each unique product.
    Returns a deduplicated DataFrame with a reset index.
    """
    before = len(df)

    # WHY sort before dedup: drop_duplicates keeps the first occurrence.
    # By sorting descending on scraped_at, the first occurrence of each
    # duplicate group will be the most recent one — exactly what we want.
    df = df.sort_values("scraped_at", ascending=False)

    dedup_keys = ["bank_name", "product_type", "product_name", "interest_rate_pct"]
    df = df.drop_duplicates(subset=dedup_keys, keep="first")

    # WHY reset_index: After dropping rows, the original row indices have gaps
    # (e.g. 0, 1, 4, 7...). Resetting gives a clean 0-based index which is
    # important for consistent CSV row numbering in step 4.
    df = df.reset_index(drop=True)

    after = len(df)
    print(f"  Removed {before - after} duplicates → {after} clean records")
    return df


# =============================================================================
# clean()  — Main entry point for this step
# =============================================================================
# WHY a wrapper function: Having a single clean() function that calls both
# standardize_formats() and remove_duplicates() keeps the interface simple for
# run_pipeline.py — it just calls clean(raw_records) and gets back a DataFrame.
# =============================================================================
def clean(records: list[dict]) -> pd.DataFrame:
    """
    Main cleaning function. Accepts raw scraped records and returns a
    fully standardised, deduplicated pandas DataFrame.
    """
    print("Cleaning data...")
    df = standardize_formats(records)
    df = remove_duplicates(df)

    # WHY print a summary: Gives the pipeline operator a quick sanity check
    # to verify the expected number of records per product type.
    print("\nRecords by product type:")
    summary = df["product_type"].value_counts()
    for ptype, count in summary.items():
        print(f"  {ptype:<25} {count}")

    # WHY report quality flags separately: Flagged records are included in the
    # output (not silently dropped) so analysts can review and decide. Printing
    # them here makes the issue visible during pipeline runs.
    suspect = df[df["data_quality"] != "ok"]
    if len(suspect):
        print(f"\nData quality flags: {len(suspect)} records flagged")
        print(suspect[["bank_name", "product_name", "data_quality"]].to_string(index=False))

    return df


# =============================================================================
# SELF-TEST
# =============================================================================
# WHY: Tests standardisation and deduplication with two identical records.
# Expected result: 1 record after dedup (the more recent one is kept).
# Run with: python step3_cleaning.py
# =============================================================================
if __name__ == "__main__":
    sample = [
        {
            "bank_name": "HSBC UAE", "product_type": "savings_account",
            "product_name": " Smart Saver ", "interest_rate_pct": 2.75,
            "min_balance_aed": 3000, "max_balance_aed": None,
            "currency": "aed", "tenure_months": 0, "fees_aed": 0,
            "eligibility": "UAE Resident", "source_url": "https://hsbc.ae",
            "scraped_at": "2025-04-01T10:00:00+00:00",  # Earlier run
        },
        {
            "bank_name": "HSBC UAE", "product_type": "savings_account",
            "product_name": " Smart Saver ", "interest_rate_pct": 2.75,
            "min_balance_aed": 3000, "max_balance_aed": None,
            "currency": "aed", "tenure_months": 0, "fees_aed": 0,
            "eligibility": "UAE Resident", "source_url": "https://hsbc.ae",
            "scraped_at": "2025-04-01T11:00:00+00:00",  # Later run — this one is kept
        },
    ]
    df = clean(sample)
    print(f"\nFinal: {len(df)} record(s) (expected 1 after dedup)")
    print(df.to_string())
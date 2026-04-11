"""
Step 3: Cleaning
- Standardize formats
- Remove duplicates
"""

import re
import pandas as pd
from datetime import datetime, timezone


def standardize_formats(records: list[dict]) -> pd.DataFrame:
    """Normalize all fields to consistent types and formats."""
    df = pd.DataFrame(records)

    # ── String fields: strip whitespace, title-case names ─────────────────────
    str_cols = ["bank_name", "product_name", "product_type", "currency", "eligibility"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df["bank_name"]    = df["bank_name"].str.title()
    df["product_name"] = df["product_name"].str.strip()
    df["product_type"] = df["product_type"].str.lower().str.replace(" ", "_")
    df["currency"]     = df["currency"].str.upper().str.strip()

    # ── Numeric fields: coerce to float, fill missing with 0 ──────────────────
    num_cols = ["interest_rate_pct", "min_balance_aed", "fees_aed", "tenure_months"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # max_balance_aed can be None (unlimited) — keep as nullable float
    if "max_balance_aed" in df.columns:
        df["max_balance_aed"] = pd.to_numeric(df["max_balance_aed"], errors="coerce")

    # ── Round numeric values ───────────────────────────────────────────────────
    df["interest_rate_pct"] = df["interest_rate_pct"].round(2)
    df["min_balance_aed"]   = df["min_balance_aed"].round(2)
    df["fees_aed"]          = df["fees_aed"].round(2)
    df["tenure_months"]     = df["tenure_months"].astype(int)

    # ── Timestamp: ensure valid ISO format ────────────────────────────────────
    def normalize_ts(ts):
        try:
            return pd.to_datetime(ts, utc=True).isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()

    df["scraped_at"] = df["scraped_at"].apply(normalize_ts)

    # ── Add a data_quality flag ────────────────────────────────────────────────
    df["data_quality"] = "ok"
    df.loc[df["interest_rate_pct"] > 50,  "data_quality"] = "suspect_rate"
    df.loc[df["min_balance_aed"] < 0,     "data_quality"] = "negative_balance"
    df.loc[df["product_name"].str.len() < 2, "data_quality"] = "missing_name"

    print(f"  Standardized {len(df)} records")
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    A duplicate = same bank + product_type + product_name + interest_rate.
    Keep the most recently scraped record.
    """
    before = len(df)

    df = df.sort_values("scraped_at", ascending=False)
    dedup_keys = ["bank_name", "product_type", "product_name", "interest_rate_pct"]
    df = df.drop_duplicates(subset=dedup_keys, keep="first")
    df = df.reset_index(drop=True)

    after = len(df)
    print(f"  Removed {before - after} duplicates → {after} clean records")
    return df


def clean(records: list[dict]) -> pd.DataFrame:
    print("Cleaning data...")
    df = standardize_formats(records)
    df = remove_duplicates(df)

    # Summary by product type
    print("\nRecords by product type:")
    summary = df["product_type"].value_counts()
    for ptype, count in summary.items():
        print(f"  {ptype:<25} {count}")

    suspect = df[df["data_quality"] != "ok"]
    if len(suspect):
        print(f"\nData quality flags: {len(suspect)} records flagged")
        print(suspect[["bank_name", "product_name", "data_quality"]].to_string(index=False))

    return df


if __name__ == "__main__":
    # Quick self-test with sample data
    sample = [
        {"bank_name": "HSBC UAE", "product_type": "savings_account", "product_name": " Smart Saver ",
         "interest_rate_pct": 2.75, "min_balance_aed": 3000, "max_balance_aed": None,
         "currency": "aed", "tenure_months": 0, "fees_aed": 0,
         "eligibility": "UAE Resident", "source_url": "https://hsbc.ae", "scraped_at": "2025-04-01T10:00:00+00:00"},
        {"bank_name": "HSBC UAE", "product_type": "savings_account", "product_name": " Smart Saver ",
         "interest_rate_pct": 2.75, "min_balance_aed": 3000, "max_balance_aed": None,
         "currency": "aed", "tenure_months": 0, "fees_aed": 0,
         "eligibility": "UAE Resident", "source_url": "https://hsbc.ae", "scraped_at": "2025-04-01T11:00:00+00:00"},
    ]
    df = clean(sample)
    print(f"\nFinal: {len(df)} record(s)")
    print(df.to_string())

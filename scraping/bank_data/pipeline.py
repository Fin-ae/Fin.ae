"""
run_pipeline.py — executes all 5 steps end to end
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from step1_sources import BANKS, PRODUCTS, FIELDS
from step2_scraper import scrape_all
from step3_cleaning import clean
from step4_output import output

def run():
    print("=" * 55)
    print("  BANK PRODUCT DATA PIPELINE")
    print("=" * 55)

    print("\n[Step 1] Sources defined")
    print(f"  Banks: {len(BANKS)}  |  Products: {len(PRODUCTS)}  |  Fields: {len(FIELDS)}")

    print("\n[Step 2] Scraping...")
    raw_records = scrape_all()

    print("\n[Step 3] Cleaning...")
    clean_df = clean(raw_records)

    print("\n[Step 4] Exporting...")
    csv_path, json_path = output(clean_df)

    print("\n[Step 5] Documentation")
    print("  step5_documentation.md — process documented")

    print("\n" + "=" * 55)
    print(f"  PIPELINE COMPLETE — {len(clean_df)} records ready")
    print("=" * 55)

    # Preview first 5 rows
    print("\nSample output (first 5 records):")
    preview_cols = ["bank_name", "product_type", "product_name", "interest_rate_pct", "min_balance_aed", "fees_aed"]
    print(clean_df[preview_cols].head(5).to_string(index=False))

    return clean_df

if __name__ == "__main__":
    run()

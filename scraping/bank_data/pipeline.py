"""
=============================================================================
RUN PIPELINE — Master Orchestrator
=============================================================================
PURPOSE:
    This is the single entry point for the entire bank product data pipeline.
    Running this file executes all 5 steps in sequence:

        Step 1 → Load source configuration (banks, products, schema)
        Step 2 → Scrape raw product data from all bank sources
        Step 3 → Clean and standardise the raw data
        Step 4 → Export clean data to CSV and JSON files
        Step 5 → Documentation (step5_documentation.md — pre-written)

    Usage:
        python run_pipeline.py

WHY A SEPARATE ORCHESTRATOR FILE:
    Keeping the orchestration logic here (rather than inside one of the step
    files) means each step module is independently testable and importable.
    A developer can run python step3_cleaning.py on its own without
    accidentally triggering a full scrape. The orchestrator is the only file
    that knows about the full sequence.

HOW THE STEPS CONNECT:
    step1  →  defines BANKS, PRODUCTS, FIELDS (imported by step2)
    step2  →  scrape_all() returns raw list[dict]
    step3  →  clean(raw_list) returns a clean pandas DataFrame
    step4  →  output(df) writes CSV + JSON to /scraping/accounts/
=============================================================================
"""

import sys
import os

# WHY sys.path.insert: Ensures Python can find the step modules in the same
# directory as this file, regardless of where the script is run from.
# Without this, running the script from a different working directory would
# raise a ModuleNotFoundError.
sys.path.insert(0, os.path.dirname(__file__))

# Import each step's main function / data
from step1_sources import BANKS, PRODUCTS, FIELDS   # Configuration
from step2_scraper import scrape_all                 # Raw data extraction
from step3_cleaning import clean                     # Data cleaning
from step4_output import output                      # File export


def run():
    """
    Executes the full pipeline from source config through to file export.
    Prints progress at each step and a summary at the end.
    Returns the clean DataFrame for optional downstream use.
    """

    # WHY print separators: Makes the console output easy to read when the
    # pipeline is run in a terminal or scheduled task log.
    print("=" * 55)
    print("  BANK PRODUCT DATA PIPELINE")
    print("=" * 55)

    # ── Step 1 ─────────────────────────────────────────────────────────────
    # WHY just print here: The actual work of step 1 is done at import time
    # (the BANKS/PRODUCTS/FIELDS constants are loaded when we import them above).
    # Here we just confirm to the operator what was loaded.
    print("\n[Step 1] Sources defined")
    print(f"  Banks: {len(BANKS)}  |  Products: {len(PRODUCTS)}  |  Fields: {len(FIELDS)}")

    # ── Step 2 ─────────────────────────────────────────────────────────────
    # WHY scrape_all() returns a flat list: A flat list of dicts is the simplest
    # structure to pass to pandas in step 3. No nesting, no special objects —
    # just plain Python dictionaries that map directly to DataFrame rows.
    print("\n[Step 2] Scraping...")
    raw_records = scrape_all()

    # ── Step 3 ─────────────────────────────────────────────────────────────
    # WHY clean() accepts list and returns DataFrame: This interface boundary
    # is intentional. Step 2 works with plain Python (no pandas dependency),
    # and step 3 is where we introduce pandas for efficient bulk transformations.
    print("\n[Step 3] Cleaning...")
    clean_df = clean(raw_records)

    # ── Step 4 ─────────────────────────────────────────────────────────────
    # WHY output() returns paths: Returning the file paths lets us log exactly
    # where the files landed, which is useful in automated/scheduled runs
    # where you need to confirm the output location.
    print("\n[Step 4] Exporting...")
    csv_path, json_path = output(clean_df)

    # ── Step 5 ─────────────────────────────────────────────────────────────
    # WHY just print here: Step 5 is documentation (step5_documentation.md).
    # It is a static file written alongside the code — no code needs to run.
    # We acknowledge it here so the operator knows all 5 steps were covered.
    print("\n[Step 5] Documentation")
    print("  step5_documentation.md — process documented")

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(f"  PIPELINE COMPLETE — {len(clean_df)} records ready")
    print("=" * 55)

    # WHY preview 5 rows: A quick sanity check that the data looks correct
    # without printing hundreds of rows to the console.
    print("\nSample output (first 5 records):")
    preview_cols = ["bank_name", "product_type", "product_name", "interest_rate_pct", "min_balance_aed", "fees_aed"]
    print(clean_df[preview_cols].head(5).to_string(index=False))

    # WHY return clean_df: Allows this function to be imported and called
    # from a notebook or another script that wants access to the DataFrame
    # without re-running the whole pipeline.
    return clean_df


# =============================================================================
# ENTRY POINT
# =============================================================================
# WHY if __name__ == "__main__": Standard Python guard that ensures run() is
# only called when this file is executed directly (python run_pipeline.py),
# not when it is imported as a module by another script.
# =============================================================================
if __name__ == "__main__":
    run()

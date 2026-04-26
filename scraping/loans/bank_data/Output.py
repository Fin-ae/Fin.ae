"""
=============================================================================
STEP 4: OUTPUT
=============================================================================
PURPOSE:
    Takes the clean DataFrame from step 3 and writes it to disk in two
    formats:
      1. CSV  — for spreadsheet tools, Excel, Power BI, and quick inspection
      2. JSON — for the AI recommendation assistant and API consumers

    Also writes one CSV per product type (e.g. fixed_deposit.csv) so
    downstream systems can load only the data they need without filtering.

WHY TWO FORMATS:
    - CSV is universally readable and easy to open in Excel or import into
      databases. It is the standard format for tabular data sharing.
    - JSON is better for the AI assistant (step 5) because it supports nested
      metadata (total record count, schema version, list of banks covered) and
      maps directly to Python/JavaScript objects without parsing overhead.

WHY TIMESTAMPED FILENAMES:
    Each pipeline run writes a new file with a UTC timestamp in the name
    (e.g. bank_products_20260411_095459.csv). This means historical runs are
    never overwritten — you can always compare rates from different dates and
    track how bank products change over time.

OUTPUT DIRECTORY: /scraping/accounts/
    All files are written to this path so they are co-located with the
    project and easy to find. The directory is created automatically if it
    does not already exist.
=============================================================================
"""

import json                             # For serialising data to JSON format
import os                               # For file system operations
import pandas as pd                     # DataFrame manipulation and CSV export
from datetime import datetime, timezone # For generating UTC timestamps in filenames
from pathlib import Path                # Cross-platform file path handling

# WHY pathlib.Path instead of os.path:
# Path objects are more readable and work on Windows, macOS, and Linux without
# needing to worry about forward vs backward slashes in directory strings.
OUTPUT_DIR = Path("/scraping/accounts")


# =============================================================================
# ensure_output_dir()
# =============================================================================
# WHY: The output directory may not exist on the first run. Rather than raising
# a FileNotFoundError, we create it automatically. parents=True creates any
# missing parent directories. exist_ok=True prevents an error if it already
# exists — making this function safe to call multiple times.
# =============================================================================
def ensure_output_dir():
    """Creates the output directory if it does not already exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Output directory ready: {OUTPUT_DIR}")


# =============================================================================
# to_csv()
# =============================================================================
# WHY CSV: Comma-Separated Values is the simplest, most portable tabular
# format. It can be opened directly in Excel, imported into SQL databases,
# and read by pandas, R, Power BI, and virtually every data tool.
#
# WHY index=False: pandas adds a row number column by default. We disable this
# because our data already has a clean 0-based index from step 3, and adding
# an extra unnamed column would confuse downstream consumers.
#
# WHY encoding="utf-8": Ensures Arabic characters, special symbols, and
# accented characters in bank names/product names are preserved correctly.
# =============================================================================
def to_csv(df: pd.DataFrame, filename: str = None) -> Path:
    """
    Writes the DataFrame to a CSV file in the output directory.
    Auto-generates a timestamped filename if none is provided.
    Returns the path of the written file.
    """
    ensure_output_dir()

    # WHY auto-generate filename: Ensures each run produces a unique file.
    # Using UTC time in the name avoids timezone confusion across servers.
    if not filename:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"bank_products_{ts}.csv"

    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8")

    # WHY report file size: Gives the operator confidence that data was
    # written and helps catch issues (e.g. a 0 KB file = empty DataFrame).
    size_kb = round(path.stat().st_size / 1024, 1)
    print(f"  CSV saved  : {path}  ({size_kb} KB, {len(df)} rows)")
    return path


# =============================================================================
# to_json()
# =============================================================================
# WHY JSON with metadata wrapper:
#   Raw JSON arrays (just a list of records) lack context. Wrapping the data
#   in a metadata envelope gives the AI assistant and any API consumer key
#   information without having to inspect the data itself:
#     - generated_at: when the data was last refreshed
#     - total_records: quick validation count
#     - banks: which institutions are covered
#     - product_types: which product categories are present
#     - schema_version: so consumers can handle schema changes gracefully
#
# WHY df.to_json + json.loads instead of df.to_dict:
#   df.to_json handles NaN → null conversion automatically (required for valid
#   JSON). We then parse it back with json.loads to get a Python list we can
#   embed in our metadata wrapper before re-serialising with json.dump.
# =============================================================================
def to_json(df: pd.DataFrame, filename: str = None) -> Path:
    """
    Writes the DataFrame to a JSON file with a metadata wrapper.
    Auto-generates a timestamped filename if none is provided.
    Returns the path of the written file.
    """
    ensure_output_dir()

    if not filename:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"bank_products_{ts}.json"

    path = OUTPUT_DIR / filename

    # WHY orient="records": Produces a list of objects [{...}, {...}] rather
    # than the default column-oriented format — much easier for APIs to consume.
    # WHY default_handler=str: Converts any remaining non-serialisable types
    # (e.g. pandas Timestamp) to strings as a safety net.
    records = json.loads(df.to_json(orient="records", date_format="iso", default_handler=str))

    output = {
        "metadata": {
            "generated_at":  datetime.now(timezone.utc).isoformat(),
            "total_records": len(records),
            "banks":         sorted(df["bank_name"].unique().tolist()),
            "product_types": sorted(df["product_type"].unique().tolist()),
            "schema_version": "1.0",  # Increment this if FIELDS schema changes
        },
        "data": records,
    }

    # WHY indent=2: Makes the JSON file human-readable for debugging.
    # WHY ensure_ascii=False: Preserves Arabic or special characters as-is
    # rather than escaping them as \uXXXX sequences.
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_kb = round(path.stat().st_size / 1024, 1)
    print(f"  JSON saved : {path}  ({size_kb} KB, {len(records)} records)")
    return path


# =============================================================================
# export_by_product_type()
# =============================================================================
# WHY per-product CSVs: The AI recommendation assistant and other consumers
# typically only need data for one product type at a time (e.g. "show me all
# fixed deposit options"). Loading a 6-product CSV and filtering in code adds
# unnecessary complexity on the consumer side. Providing pre-split files makes
# integration simpler and faster.
# =============================================================================
def export_by_product_type(df: pd.DataFrame):
    """
    Writes one CSV file per product type to the output directory.
    e.g. fixed_deposit.csv, credit_card.csv, savings_account.csv
    These are overwritten on each run since they always reflect current data.
    """
    for ptype in df["product_type"].unique():
        subset = df[df["product_type"] == ptype].copy()
        fname = f"{ptype}.csv"
        path = OUTPUT_DIR / fname
        subset.to_csv(path, index=False, encoding="utf-8")
        print(f"  Product CSV: {path}  ({len(subset)} rows)")


# =============================================================================
# output()  — Main entry point for this step
# =============================================================================
# WHY a wrapper: Keeps run_pipeline.py simple — it just calls output(df) and
# all three export formats are handled in one call.
# =============================================================================
def output(df: pd.DataFrame):
    """
    Runs all three export operations: full CSV, full JSON, and per-product CSVs.
    Returns paths to the main CSV and JSON files for logging in run_pipeline.py.
    """
    print("Exporting data...")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path  = to_csv(df,  f"bank_products_{ts}.csv")
    json_path = to_json(df, f"bank_products_{ts}.json")
    export_by_product_type(df)
    print(f"\nAll files written to: {OUTPUT_DIR}")
    return csv_path, json_path


# =============================================================================
# SELF-TEST
# =============================================================================
# WHY: Lets a developer test the export functions in isolation with a minimal
# one-row DataFrame before running the full pipeline.
# Run with: python step4_output.py
# =============================================================================
if __name__ == "__main__":
    sample_df = pd.DataFrame([{
        "bank_name": "HSBC UAE", "product_type": "savings_account",
        "product_name": "Smart Saver", "interest_rate_pct": 2.75,
        "min_balance_aed": 3000.0, "max_balance_aed": None,
        "currency": "AED", "tenure_months": 0, "fees_aed": 0.0,
        "eligibility": "UAE Resident", "source_url": "https://hsbc.ae",
        "scraped_at": "2025-04-01T10:00:00+00:00", "data_quality": "ok",
    }])
    output(sample_df)
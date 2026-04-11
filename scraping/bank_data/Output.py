"""
Step 4: Output
- Convert to JSON/CSV
- Upload to /scraping/accounts/
"""

import json
import os
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path("/scraping/accounts")


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Output directory ready: {OUTPUT_DIR}")


def to_csv(df: pd.DataFrame, filename: str = None) -> Path:
    ensure_output_dir()
    if not filename:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"bank_products_{ts}.csv"

    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8")
    size_kb = round(path.stat().st_size / 1024, 1)
    print(f"  CSV saved  : {path}  ({size_kb} KB, {len(df)} rows)")
    return path


def to_json(df: pd.DataFrame, filename: str = None) -> Path:
    ensure_output_dir()
    if not filename:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"bank_products_{ts}.json"

    path = OUTPUT_DIR / filename

    # Convert DataFrame to list of dicts; handle NaN → None for valid JSON
    records = json.loads(df.to_json(orient="records", date_format="iso", default_handler=str))

    output = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(records),
            "banks": sorted(df["bank_name"].unique().tolist()),
            "product_types": sorted(df["product_type"].unique().tolist()),
            "schema_version": "1.0",
        },
        "data": records,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_kb = round(path.stat().st_size / 1024, 1)
    print(f"  JSON saved : {path}  ({size_kb} KB, {len(records)} records)")
    return path


def export_by_product_type(df: pd.DataFrame):
    """Also write one CSV per product type for easy downstream consumption."""
    for ptype in df["product_type"].unique():
        subset = df[df["product_type"] == ptype].copy()
        fname = f"{ptype}.csv"
        path = OUTPUT_DIR / fname
        subset.to_csv(path, index=False, encoding="utf-8")
        print(f"  Product CSV: {path}  ({len(subset)} rows)")


def output(df: pd.DataFrame):
    print("Exporting data...")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path  = to_csv(df,  f"bank_products_{ts}.csv")
    json_path = to_json(df, f"bank_products_{ts}.json")
    export_by_product_type(df)
    print(f"\nAll files written to: {OUTPUT_DIR}")
    return csv_path, json_path


if __name__ == "__main__":
    # Quick self-test with sample data
    sample_df = pd.DataFrame([
        {"bank_name": "HSBC UAE", "product_type": "savings_account", "product_name": "Smart Saver",
         "interest_rate_pct": 2.75, "min_balance_aed": 3000.0, "max_balance_aed": None,
         "currency": "AED", "tenure_months": 0, "fees_aed": 0.0,
         "eligibility": "UAE Resident", "source_url": "https://hsbc.ae",
         "scraped_at": "2025-04-01T10:00:00+00:00", "data_quality": "ok"},
    ])
    output(sample_df)

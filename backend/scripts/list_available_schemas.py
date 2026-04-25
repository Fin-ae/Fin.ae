"""
List available department schemas (collections) that already exist in MongoDB.

This script reads MONGO_URL and DB_NAME from backend/.env.

Usage:
    python backend/scripts/list_available_schemas.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote_plus, unquote

from dotenv import load_dotenv
from pymongo import MongoClient


SUPPORTED_SCHEMA_LABELS = {
    "policies_insurance": "Insurance",
    "policies_loans": "Loans",
    "policies_credit_cards": "Credit Cards",
    "policies_investments": "Investments",
    "policies_bank_accounts": "Bank Accounts",
    "policies": "Legacy Combined Policies",
}


def _encode_mongo_url(url: str) -> str:
    scheme_match = re.match(r"^(mongodb(?:\+srv)?://)", url)
    if not scheme_match:
        return url
    scheme = scheme_match.group(1)
    rest = url[len(scheme) :]
    at_idx = rest.rfind("@")
    if at_idx == -1:
        return url
    userinfo, hostinfo = rest[:at_idx], rest[at_idx + 1 :]
    colon_idx = userinfo.find(":")
    if colon_idx == -1:
        return url
    user, password = userinfo[:colon_idx], userinfo[colon_idx + 1 :]
    return f"{scheme}{quote_plus(unquote(user))}:{quote_plus(unquote(password))}@{hostinfo}"


def _load_env() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    load_dotenv(backend_dir / ".env")


def main() -> None:
    _load_env()

    mongo_url = os.getenv("MONGO_URL", "").strip()
    db_name = os.getenv("DB_NAME", "").strip()

    if not mongo_url or not db_name:
        print("Error: MONGO_URL or DB_NAME not found in backend/.env")
        return

    client = MongoClient(_encode_mongo_url(mongo_url))
    try:
        db = client[db_name]
        existing = set(db.list_collection_names())

        available = [name for name in SUPPORTED_SCHEMA_LABELS if name in existing]

        if not available:
            print("No supported department schemas found in this database.")
            print("Expected one or more of:")
            for name in SUPPORTED_SCHEMA_LABELS:
                print(f"- {name}")
            return

        print("Available schemas (present in DB):")
        for name in available:
            count = db[name].count_documents({})
            label = SUPPORTED_SCHEMA_LABELS[name]
            print(f"- {name} ({label}) -> {count} records")
    finally:
        client.close()


if __name__ == "__main__":
    main()

"""
Import JSON data into a selected existing department schema in MongoDB.

Designed for data-entry users:
- Reads secrets from backend/.env (MONGO_URL, DB_NAME)
- Shows only schema names that already exist in the DB
- Lets user select schema and JSON path interactively

Supported JSON formats:
- A list of objects
- A single object
- An object with one of: data, items, records (list)

Examples:
    python backend/scripts/import_department_json.py
    python backend/scripts/import_department_json.py --schema policies_loans --file /path/to/loans.json --mode append
    python backend/scripts/import_department_json.py --schema policies_insurance --file /path/to/insurance.json --mode replace --yes
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, unquote

from dotenv import load_dotenv
from pymongo import MongoClient, ReplaceOne, InsertOne
from pymongo.errors import BulkWriteError


SUPPORTED_SCHEMA_LABELS = {
    "policies_insurance": "Insurance",
    "policies_loans": "Loans",
    "policies_credit_cards": "Credit Cards",
    "policies_investments": "Investments",
    "policies_bank_accounts": "Bank Accounts",
    "policies": "Legacy Combined Policies",
}

# Optional one-line default. Set to a schema name like "policies_loans".
DEFAULT_SCHEMA = ""


def _normalize_schema_name(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""

    # Accept exact collection name.
    if raw in SUPPORTED_SCHEMA_LABELS:
        return raw

    # Accept human-friendly label (case-insensitive), e.g. "Insurance".
    lowered = raw.lower()
    for key, label in SUPPORTED_SCHEMA_LABELS.items():
        if label.lower() == lowered:
            return key

    return raw


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


def _load_env() -> tuple[str, str]:
    backend_dir = Path(__file__).resolve().parents[1]
    load_dotenv(backend_dir / ".env")

    mongo_url = os.getenv("MONGO_URL", "").strip()
    db_name = os.getenv("DB_NAME", "").strip()

    if not mongo_url or not db_name:
        raise RuntimeError("MONGO_URL or DB_NAME not found in backend/.env")

    return _encode_mongo_url(mongo_url), db_name


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        for key in ("data", "items", "records"):
            if key in payload and isinstance(payload[key], list):
                records = payload[key]
                break
        else:
            records = [payload]
    else:
        raise ValueError("JSON root must be a list or object.")

    cleaned: list[dict[str, Any]] = []
    for idx, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"Record #{idx} is not a JSON object.")
        item = dict(record)
        item.pop("_id", None)
        cleaned.append(item)

    return cleaned


def _load_json_file(file_path: Path) -> list[dict[str, Any]]:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    records = _extract_records(payload)
    if not records:
        raise ValueError("No records found in JSON file.")

    return records


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import JSON into an existing MongoDB department schema")
    parser.add_argument("--schema", help="Target schema/collection name (example: policies_loans)")
    parser.add_argument("--file", dest="file_path", help="Path to JSON file")
    parser.add_argument(
        "--mode",
        choices=["append", "replace"],
        default="append",
        help="append: insert new records, replace: clear collection before insert",
    )
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
    return parser.parse_args()


def _prompt_choice(options: list[str], title: str) -> str:
    print(title)
    for i, name in enumerate(options, start=1):
        print(f"  {i}. {name}")

    while True:
        raw = input("Enter number: ").strip()
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        print("Invalid selection. Try again.")


def _confirm(question: str) -> bool:
    answer = input(f"{question} [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def _resolve_path(raw_path: str) -> Path:
    """Resolve path, handling Windows-style absolute paths in WSL."""
    path_str = raw_path.strip().strip('"')
    
    # Handle Windows absolute paths (e.g. C:\Users\... or C:/Users/...) when running on Linux/WSL
    if os.name != 'nt' and re.match(r'^[a-zA-Z]:[\\/]', path_str):
        # Convert C:\foo\bar to /mnt/c/foo/bar
        drive = path_str[0].lower()
        parts = path_str[3:].replace('\\', '/')
        path_str = f"/mnt/{drive}/{parts}"
    
    return Path(path_str).expanduser().resolve()


def _prompt_file_path() -> Path:
    while True:
        raw_path = input("Enter JSON file path: ").strip()
        if not raw_path:
            print("Path cannot be empty. Try again.")
            continue

        file_path = _resolve_path(raw_path)
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue
        if not file_path.is_file():
            print(f"Not a file: {file_path}")
            continue
        return file_path


def main() -> None:
    args = _parse_args()

    try:
        mongo_url, db_name = _load_env()
    except Exception as exc:
        print(f"Error: {exc}")
        return

    client = MongoClient(mongo_url)

    try:
        db = client[db_name]
        existing = set(db.list_collection_names())
        available_schemas = [name for name in SUPPORTED_SCHEMA_LABELS if name in existing]

        if not available_schemas:
            print("No supported schemas found in this database.")
            return

        for name in available_schemas:
            label = SUPPORTED_SCHEMA_LABELS[name]
            count = db[name].count_documents({})
            print(f"- {name} ({label}) -> {count} records")

        schema = _normalize_schema_name(args.schema or DEFAULT_SCHEMA)
        if schema:
            if schema not in available_schemas:
                print(f"Error: '{schema}' is not present in the database.")
                print("Choose from available schemas only.")
                return
        else:
            schema = _prompt_choice(available_schemas, "\nSelect target schema:")

        if args.file_path:
            file_path = _resolve_path(args.file_path)
        else:
            file_path = _prompt_file_path()

        try:
            records = _load_json_file(file_path)
        except Exception as exc:
            print(f"Error reading JSON: {exc}")
            return

        print("\nImport summary:")
        print(f"- Database: {db_name}")
        print(f"- Schema: {schema}")
        print(f"- Mode: {args.mode}")
        print(f"- File: {file_path}")
        print(f"- Records in file: {len(records)}")

        collection = db[schema]

        if args.mode == "replace":
            if not args.yes and not _confirm("This will DELETE existing records in the target schema. Continue?"):
                print("Cancelled.")
                return
            deleted = collection.delete_many({}).deleted_count
            print(f"Deleted existing records: {deleted}")

        if not args.yes and not _confirm("Proceed with import?"):
            print("Cancelled.")
            return

        try:
            operations = []
            for record in records:
                if "policy_id" in record:
                    operations.append(ReplaceOne({"policy_id": record["policy_id"]}, record, upsert=True))
                else:
                    operations.append(InsertOne(record))
            
            result = collection.bulk_write(operations, ordered=False)
            inserted_count = result.upserted_count + result.inserted_count + result.modified_count
            failed_count = 0
        except BulkWriteError as exc:
            details = exc.details or {}
            write_errors = details.get("writeErrors", [])
            inserted_count = details.get("nInserted", 0)
            failed_count = len(write_errors)
            print(f"Import completed with partial failures. Failed records: {failed_count}")
            for i, err in enumerate(write_errors[:5]):
                errmsg = err.get('errmsg', str(err))
                err_info = err.get('errInfo', {})
                if err_info:
                    print(f"  Error {i+1}: {errmsg} | Details: {err_info}")
                else:
                    print(f"  Error {i+1}: {errmsg}")
            if failed_count > 5:
                print(f"  ... and {failed_count - 5} more errors.")

        final_count = collection.count_documents({})
        print("\nDone.")
        print(f"- Inserted: {inserted_count}")
        print(f"- Failed: {failed_count}")
        print(f"- Final schema record count: {final_count}")

    finally:
        client.close()


if __name__ == "__main__":
    main()

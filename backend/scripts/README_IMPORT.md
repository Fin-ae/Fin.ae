# Department Data Import Scripts

These scripts are for data-entry users to import department JSON files into MongoDB.

## 1) List available schemas in DB

This shows only schemas that already exist in your database.

```bash
python backend/scripts/list_available_schemas.py
```

## 2) Import JSON into a selected schema

Interactive mode (recommended):

```bash
python backend/scripts/import_department_json.py
```

Windows direct launcher (no `python` needed):

```bat
backend\\scripts\\import_department_json.bat
```

Non-interactive mode:

```bash
python backend/scripts/import_department_json.py --schema policies_loans --file /path/to/loans.json --mode append
```

Replace mode (deletes existing data first):

```bash
python backend/scripts/import_department_json.py --schema policies_insurance --file /path/to/insurance.json --mode replace --yes
```

## JSON formats supported

- List of objects
- Single object
- Object containing one of these list keys:
  - `data`
  - `items`
  - `records`

Examples:

```json
[
  {"policy_id": "loan-101", "category": "loan", "name": "Sample Loan", "provider": "ABC Bank", "features": {"rate": "4%"}}
]
```

```json
{
  "records": [
    {"policy_id": "ins-201", "category": "insurance", "name": "Sample Insurance", "provider": "XYZ Insurance", "features": {"coverage": "AED 1M"}}
  ]
}
```

## Environment

Both scripts read MongoDB settings from:

- `backend/.env`
  - `MONGO_URL`
  - `DB_NAME`

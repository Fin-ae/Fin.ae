# ══════════════════════════════════════════════════════
#  Fin.ae — Loan API
#  Author: [Your Name]
#  Task 2: API Design & Development
#  Database: loan_data.db (from Task 1 scraping)
# ══════════════════════════════════════════════════════

from flask import Flask, jsonify, request
import sqlite3
import hashlib
import urllib.request
import json
from datetime import datetime

sqlite3.register_adapter(datetime, lambda d: d.isoformat())

app = Flask(__name__)

# ── Points to your Task 1 loan database ───────────────
DB_PATH = "../scraping/loans/loan_data.db"

# ── DB HELPER ──────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ══════════════════════════════════════════════════════
#  ENDPOINT 1 — GET /products
#  Returns all loan products from your scraped database
# ══════════════════════════════════════════════════════
@app.route("/products", methods=["GET"])
def get_products():
    conn = get_db()
    cursor = conn.cursor()

    # Get all table names in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    result = {}
    total = 0
    for table in tables:
        rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
        result[table] = [dict(row) for row in rows]
        total += len(result[table])

    conn.close()
    return jsonify({
        "status": "success",
        "data": result,
        "total_products": total,
        "tables_found": tables
    })

# ══════════════════════════════════════════════════════
#  ENDPOINT 2 — POST /user/register
#  Saves a new user profile
# ══════════════════════════════════════════════════════
@app.route("/user/register", methods=["POST"])
def register_user():
    data = request.get_json()

    required = ["full_name", "email", "password", "monthly_salary",
                "age", "nationality", "residency_status"]
    for field in required:
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"Missing field: {field}"
            }), 400

    password_hash = hashlib.sha256(data["password"].encode()).hexdigest()
    islamic = 1 if data.get("islamic_preference") else 0

    try:
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email            TEXT NOT NULL UNIQUE,
                password_hash    TEXT NOT NULL,
                full_name        TEXT NOT NULL,
                nationality      TEXT,
                monthly_salary   REAL,
                age              INTEGER,
                residency_status TEXT,
                islamic_preference INTEGER DEFAULT 0,
                created_at       TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO users
            (email, password_hash, full_name, nationality,
             monthly_salary, age, residency_status, islamic_preference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["email"], password_hash, data["full_name"],
            data["nationality"], data["monthly_salary"],
            data["age"], data["residency_status"], islamic
        ))
        conn.commit()
        conn.close()
        return jsonify({
            "status":  "success",
            "message": "User registered successfully",
            "email":   data["email"]
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "status":  "error",
            "message": "Email already registered"
        }), 409

# ══════════════════════════════════════════════════════
#  ENDPOINT 3 — POST /leads
#  Saves when a user clicks Apply on a loan product
# ══════════════════════════════════════════════════════
@app.route("/leads", methods=["POST"])
def submit_lead():
    data = request.get_json()

    required = ["user_id", "product_id"]
    for field in required:
        if field not in data:
            return jsonify({
                "status":  "error",
                "message": f"Missing field: {field}"
            }), 400

    try:
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                lead_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                product_id   INTEGER NOT NULL,
                service_type TEXT DEFAULT 'loan',
                status       TEXT DEFAULT 'Pending',
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO leads (user_id, product_id, service_type, status)
            VALUES (?, ?, 'loan', 'Pending')
        """, (data["user_id"], data["product_id"]))
        conn.commit()
        conn.close()
        return jsonify({
            "status":     "success",
            "message":    "Lead submitted successfully",
            "product_id": data["product_id"]
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ══════════════════════════════════════════════════════
#  ENDPOINT 4 — GET /recommendations
#  Returns ranked loans based on user salary profile
# ══════════════════════════════════════════════════════
@app.route("/recommendations", methods=["GET"])
def get_recommendations():
    try:
        salary  = float(request.args.get("salary", 0))
        islamic = int(request.args.get("islamic", 0))
    except ValueError:
        return jsonify({
            "status":  "error",
            "message": "Invalid parameters — salary must be a number"
        }), 400

    if salary <= 0:
        return jsonify({
            "status":  "error",
            "message": "Please provide salary as a query parameter e.g. ?salary=8000"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    # Get all tables and look for loan data
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    all_loans = []
    for table in tables:
        if table in ["users", "leads"]:
            continue
        try:
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                loan = dict(row)
                loan["source_table"] = table

                # ── Scoring logic ──────────────────────
                score = 0
                rate = loan.get("rate") or loan.get("interest_rate") or 999
                min_sal = loan.get("salary") or loan.get("min_salary") or 0

                if salary >= float(min_sal):             score += 40
                if float(rate) < 5:                      score += 30
                elif float(rate) < 8:                    score += 20
                elif float(rate) < 12:                   score += 10
                if loan.get("islamic") == islamic:       score += 20
                loan["recommendation_score"] = score
                all_loans.append(loan)
        except Exception:
            continue

    conn.close()

    # Sort by score — best first
    all_loans.sort(key=lambda x: x["recommendation_score"], reverse=True)

    return jsonify({
        "status":           "success",
        "user_profile":     {"salary": salary, "islamic": islamic},
        "recommendations":  all_loans[:5],
        "total_found":      len(all_loans)
    })

# ══════════════════════════════════════════════════════
#  ENDPOINT 5 — GET /rates
#  Returns live AED exchange rates from professor's API
# ══════════════════════════════════════════════════════
@app.route("/rates", methods=["GET"])
def get_rates():
    try:
        API_KEY = "b374490def46a81aec82416c"
        url     = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/AED"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())

        # Filter to expat-relevant currencies only
        expat_currencies = ["INR", "PKR", "PHP", "EGP", "BDT",
                            "LKR", "NPR", "USD", "GBP", "EUR"]
        filtered = {k: v for k, v in data["conversion_rates"].items()
                    if k in expat_currencies}

        return jsonify({
            "status":     "success",
            "base":       "AED",
            "rates":      filtered,
            "source":     "live — ExchangeRate-API v6",
            "fetched_at": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status":  "error",
            "message": f"Could not fetch rates: {str(e)}"
        }), 500

# ══════════════════════════════════════════════════════
#  HEALTH CHECK — GET /
# ══════════════════════════════════════════════════════
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status":    "running",
        "app":       "Fin.ae Loan API",
        "author":    "Task 2 — API Design & Development",
        "version":   "1.0",
        "database":  "loan_data.db (Task 1 output)",
        "endpoints": {
            "GET  /":                                "Health check",
            "GET  /products":                        "All loan products",
            "POST /user/register":                   "Register a user",
            "POST /leads":                           "Submit a lead",
            "GET  /recommendations?salary=8000":     "Ranked loan recommendations",
            "GET  /rates":                           "Live AED exchange rates"
        }
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)
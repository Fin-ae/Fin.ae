"""
Standalone policy seeder.
Reads MONGO_URL (and DB_NAME) from .env, drops the existing policies
collection, and re-inserts all 27 policies from FINANCIAL_POLICIES.

Usage:
    python backend/seed_policies.py
    python backend/seed_policies.py --force   # drop & re-seed even if data exists
"""

import asyncio
import re
import sys
from urllib.parse import quote_plus, unquote

from dotenv import load_dotenv
import os

load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient

# ── Re-use the same URL encoder from server.py ─────────────────────────────

def _encode_mongo_url(url: str) -> str:
    scheme_match = re.match(r'^(mongodb(?:\+srv)?://)', url)
    if not scheme_match:
        return url
    scheme = scheme_match.group(1)
    rest = url[len(scheme):]
    at_idx = rest.rfind('@')
    if at_idx == -1:
        return url
    userinfo, hostinfo = rest[:at_idx], rest[at_idx + 1:]
    colon_idx = userinfo.find(':')
    if colon_idx == -1:
        return url
    user, password = userinfo[:colon_idx], userinfo[colon_idx + 1:]
    return f"{scheme}{quote_plus(unquote(user))}:{quote_plus(unquote(password))}@{hostinfo}"


MONGO_URL = _encode_mongo_url(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
DB_NAME   = os.environ.get("DB_NAME", "finae")

# ── Policies ───────────────────────────────────────────────────────────────

FINANCIAL_POLICIES = [
    # ── Insurance ──────────────────────────────────────────────────────────
    {
        "policy_id": "ins-001",
        "category": "insurance",
        "sub_category": "health",
        "name": "ADNIC Premium Health Cover",
        "provider": "Abu Dhabi National Insurance Company",
        "description": "Comprehensive health insurance with worldwide coverage, dental, optical, and maternity benefits.",
        "min_salary": 8000, "min_age": 18, "max_age": 65, "risk_level": "low",
        "monthly_cost": 450, "annual_cost": 5000,
        "benefits": ["Worldwide coverage", "Dental & optical", "Maternity benefits", "No claim bonus", "Wellness programs"],
        "tenure_months": 12, "sharia_compliant": False, "rating": 4.5,
        "features": {"coverage_limit": "AED 1,000,000", "deductible": "AED 500", "network": "300+ hospitals"},
    },
    {
        "policy_id": "ins-002",
        "category": "insurance",
        "sub_category": "health",
        "name": "Takaful Emarat Family Shield",
        "provider": "Takaful Emarat",
        "description": "Sharia-compliant family health insurance with comprehensive inpatient and outpatient coverage.",
        "min_salary": 5000, "min_age": 21, "max_age": 60, "risk_level": "low",
        "monthly_cost": 350, "annual_cost": 3800,
        "benefits": ["Sharia compliant", "Family coverage", "Outpatient care", "Prescription drugs", "Annual health check"],
        "tenure_months": 12, "sharia_compliant": True, "rating": 4.3,
        "features": {"coverage_limit": "AED 500,000", "deductible": "AED 200", "network": "200+ hospitals"},
    },
    {
        "policy_id": "ins-003",
        "category": "insurance",
        "sub_category": "life",
        "name": "MetLife SecureLife Plan",
        "provider": "MetLife UAE",
        "description": "Term life insurance with critical illness cover and accidental death benefit.",
        "min_salary": 10000, "min_age": 25, "max_age": 55, "risk_level": "low",
        "monthly_cost": 200, "annual_cost": 2200,
        "benefits": ["Critical illness cover", "Accidental death benefit", "Premium waiver", "Repatriation cover"],
        "tenure_months": 120, "sharia_compliant": False, "rating": 4.6,
        "features": {"coverage_limit": "AED 2,000,000", "premium_term": "10 years", "payout": "Lump sum"},
    },
    {
        "policy_id": "ins-004",
        "category": "insurance",
        "sub_category": "motor",
        "name": "AXA Comprehensive Motor Shield",
        "provider": "AXA Gulf",
        "description": "Comprehensive motor insurance with agency repairs, roadside assistance, and personal accident cover.",
        "min_salary": 3000, "min_age": 21, "max_age": 65, "risk_level": "low",
        "monthly_cost": 200, "annual_cost": 2200,
        "benefits": ["Agency repairs", "24/7 roadside assistance", "Personal accident cover", "Hire car while in repair", "GCC coverage"],
        "tenure_months": 12, "sharia_compliant": False, "rating": 4.4,
        "features": {"coverage_limit": "Third party unlimited", "deductible": "AED 1,000", "gcc_coverage": "Yes", "roadside": "24/7"},
    },
    {
        "policy_id": "ins-005",
        "category": "insurance",
        "sub_category": "travel",
        "name": "Oman Insurance Travel Guard",
        "provider": "Oman Insurance Company",
        "description": "Comprehensive travel insurance covering medical emergencies, trip cancellation, baggage loss and flight delays.",
        "min_salary": 3000, "min_age": 18, "max_age": 70, "risk_level": "low",
        "monthly_cost": None, "annual_cost": 500,
        "benefits": ["Medical cover up to USD 1M", "Trip cancellation", "Baggage loss", "Flight delay compensation", "Adventure sports rider available"],
        "tenure_months": 12, "sharia_compliant": False, "rating": 4.2,
        "features": {"medical_cover": "USD 1,000,000", "cancellation": "Up to AED 10,000", "baggage": "Up to AED 5,000", "family_plan": "Available"},
    },
    {
        "policy_id": "ins-006",
        "category": "insurance",
        "sub_category": "home",
        "name": "RSA Home Protect Plus",
        "provider": "RSA Insurance",
        "description": "All-risks home contents and building insurance protecting against fire, theft, flood and accidental damage.",
        "min_salary": 5000, "min_age": 18, "max_age": 70, "risk_level": "low",
        "monthly_cost": 80, "annual_cost": 900,
        "benefits": ["Building & contents cover", "Theft & burglary", "Accidental damage", "Domestic helper cover", "Alternative accommodation"],
        "tenure_months": 12, "sharia_compliant": False, "rating": 4.1,
        "features": {"building_limit": "AED 3,000,000", "contents_limit": "AED 500,000", "deductible": "AED 500", "helper_cover": "Up to AED 50,000"},
    },
    # ── Loans ──────────────────────────────────────────────────────────────
    {
        "policy_id": "loan-001",
        "category": "loan",
        "sub_category": "personal",
        "name": "Emirates NBD Personal Loan",
        "provider": "Emirates NBD",
        "description": "Competitive personal loan with salary transfer, up to AED 3 million with flexible tenure.",
        "min_salary": 5000, "min_age": 21, "max_age": 60, "risk_level": "medium",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["Up to AED 3M", "Flexible tenure 12-48 months", "Quick approval", "No guarantor needed"],
        "tenure_months": 48, "sharia_compliant": False, "rating": 4.4,
        "features": {"interest_rate": "3.99% flat", "max_amount": "AED 3,000,000", "processing_fee": "1%", "min_tenure": "12 months"},
    },
    {
        "policy_id": "loan-002",
        "category": "loan",
        "sub_category": "personal",
        "name": "Dubai Islamic Bank Personal Finance",
        "provider": "Dubai Islamic Bank",
        "description": "Sharia-compliant personal finance with competitive profit rates and salary transfer benefit.",
        "min_salary": 5000, "min_age": 21, "max_age": 60, "risk_level": "medium",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["Sharia compliant", "Up to AED 2.5M", "Salary transfer benefit", "Life Takaful included"],
        "tenure_months": 48, "sharia_compliant": True, "rating": 4.3,
        "features": {"profit_rate": "4.25% flat", "max_amount": "AED 2,500,000", "processing_fee": "1.05%", "min_tenure": "12 months"},
    },
    {
        "policy_id": "loan-003",
        "category": "loan",
        "sub_category": "home",
        "name": "HSBC Home Mortgage",
        "provider": "HSBC UAE",
        "description": "Home mortgage for UAE residents with competitive rates and up to 80% financing.",
        "min_salary": 15000, "min_age": 25, "max_age": 60, "risk_level": "medium",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["Up to 80% financing", "Fixed rate options", "Property valuation included", "Free property insurance year 1"],
        "tenure_months": 300, "sharia_compliant": False, "rating": 4.5,
        "features": {"interest_rate": "3.49% variable", "max_amount": "AED 15,000,000", "ltv": "80%", "min_tenure": "60 months"},
    },
    {
        "policy_id": "loan-004",
        "category": "loan",
        "sub_category": "personal",
        "name": "ADCB TouchPoints Personal Loan",
        "provider": "Abu Dhabi Commercial Bank",
        "description": "Personal loan with TouchPoints rewards on every repayment, quick disbursement and flexible tenure.",
        "min_salary": 8000, "min_age": 21, "max_age": 60, "risk_level": "medium",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["TouchPoints on repayments", "Same-day approval", "Up to AED 1.5M", "No early settlement fee after 12 months"],
        "tenure_months": 48, "sharia_compliant": False, "rating": 4.3,
        "features": {"interest_rate": "4.49% flat", "max_amount": "AED 1,500,000", "processing_fee": "1%", "early_settlement": "Free after 12 months"},
    },
    {
        "policy_id": "loan-005",
        "category": "loan",
        "sub_category": "personal",
        "name": "Mashreq Salary Transfer Loan",
        "provider": "Mashreq Bank",
        "description": "Competitive personal loan exclusively for salary transfer customers with preferential rates and instant approval.",
        "min_salary": 5000, "min_age": 21, "max_age": 60, "risk_level": "medium",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["Preferential salary transfer rate", "Instant online approval", "Up to AED 1M", "Free life insurance", "Zero processing fee"],
        "tenure_months": 48, "sharia_compliant": False, "rating": 4.2,
        "features": {"interest_rate": "3.75% flat", "max_amount": "AED 1,000,000", "processing_fee": "0%", "insurance": "Free life cover"},
    },
    {
        "policy_id": "loan-006",
        "category": "loan",
        "sub_category": "auto",
        "name": "FAB Auto Finance",
        "provider": "First Abu Dhabi Bank",
        "description": "New and used car finance with up to 80% LTV, competitive rates and quick approval for UAE residents.",
        "min_salary": 7000, "min_age": 21, "max_age": 60, "risk_level": "medium",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["Up to 80% vehicle value", "New & used cars", "Flexible 12-60 month tenure", "Insurance bundling option"],
        "tenure_months": 60, "sharia_compliant": False, "rating": 4.3,
        "features": {"interest_rate": "3.25% flat", "max_amount": "AED 1,000,000", "ltv": "80%", "processing_fee": "1%"},
    },
    # ── Credit Cards ───────────────────────────────────────────────────────
    {
        "policy_id": "cc-001",
        "category": "credit_card",
        "sub_category": "rewards",
        "name": "FAB Rewards World Elite Mastercard",
        "provider": "First Abu Dhabi Bank",
        "description": "Premium rewards credit card with airport lounge access and travel benefits.",
        "min_salary": 15000, "min_age": 21, "max_age": 65, "risk_level": "low",
        "monthly_cost": None, "annual_cost": 500,
        "benefits": ["Unlimited lounge access", "3x reward points on travel", "Free travel insurance", "Concierge service"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.7,
        "features": {"annual_fee": "AED 500", "reward_rate": "3x on travel", "credit_limit": "Up to AED 500,000", "cashback": "1%"},
    },
    {
        "policy_id": "cc-002",
        "category": "credit_card",
        "sub_category": "cashback",
        "name": "Mashreq Cashback Card",
        "provider": "Mashreq Bank",
        "description": "Everyday cashback credit card with no annual fee for the first year.",
        "min_salary": 8000, "min_age": 21, "max_age": 65, "risk_level": "low",
        "monthly_cost": None, "annual_cost": 0,
        "benefits": ["5% cashback on dining", "3% on groceries", "1% on everything else", "Free for first year"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.2,
        "features": {"annual_fee": "AED 0 (first year)", "reward_rate": "Up to 5%", "credit_limit": "Up to AED 200,000", "cashback": "5% dining"},
    },
    {
        "policy_id": "cc-003",
        "category": "credit_card",
        "sub_category": "travel",
        "name": "Emirates NBD Skywards Signature",
        "provider": "Emirates NBD",
        "description": "Premium travel credit card that earns Skywards Miles on every spend, with airport lounge access and travel insurance.",
        "min_salary": 10000, "min_age": 21, "max_age": 65, "risk_level": "low",
        "monthly_cost": None, "annual_cost": 400,
        "benefits": ["3 Skywards Miles per AED spent", "Unlimited lounge access", "Complimentary travel insurance", "Golf privileges", "No foreign transaction fees"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.6,
        "features": {"annual_fee": "AED 400", "reward_rate": "3 miles/AED", "credit_limit": "Up to AED 300,000", "lounge": "Unlimited LoungeKey"},
    },
    {
        "policy_id": "cc-004",
        "category": "credit_card",
        "sub_category": "islamic",
        "name": "DIB Cashback Credit Card",
        "provider": "Dubai Islamic Bank",
        "description": "Sharia-compliant credit card offering cashback on everyday categories with zero interest on monthly repayment.",
        "min_salary": 5000, "min_age": 21, "max_age": 65, "risk_level": "low",
        "monthly_cost": None, "annual_cost": 0,
        "benefits": ["Sharia compliant", "5% cashback on fuel", "3% on supermarkets", "2% on utilities", "No annual fee for first year"],
        "tenure_months": None, "sharia_compliant": True, "rating": 4.1,
        "features": {"annual_fee": "AED 0 (first year)", "reward_rate": "Up to 5% cashback", "credit_limit": "Up to AED 150,000", "cashback_cap": "AED 500/month"},
    },
    {
        "policy_id": "cc-005",
        "category": "credit_card",
        "sub_category": "lifestyle",
        "name": "ADCB SimplyLife Cashback Card",
        "provider": "Abu Dhabi Commercial Bank",
        "description": "Entry-level cashback card with no annual fee, ideal for everyday spending with instant cashback rewards.",
        "min_salary": 5000, "min_age": 21, "max_age": 65, "risk_level": "low",
        "monthly_cost": None, "annual_cost": 0,
        "benefits": ["No annual fee", "2% cashback on online shopping", "1% on all other spend", "Contactless payments", "Free supplementary cards"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.0,
        "features": {"annual_fee": "AED 0", "reward_rate": "Up to 2%", "credit_limit": "Up to AED 100,000", "supplementary_cards": "3 free"},
    },
    # ── Investments ────────────────────────────────────────────────────────
    {
        "policy_id": "inv-001",
        "category": "investment",
        "sub_category": "mutual_fund",
        "name": "Emirates NBD Global Equity Fund",
        "provider": "Emirates NBD Asset Management",
        "description": "Diversified global equity fund targeting long-term capital growth.",
        "min_salary": 10000, "min_age": 21, "max_age": 70, "risk_level": "high",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["Global diversification", "Professional management", "Quarterly reporting", "Online access"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.1,
        "features": {"min_investment": "AED 10,000", "management_fee": "1.5%", "expected_return": "8-12% p.a.", "risk_rating": "High"},
    },
    {
        "policy_id": "inv-002",
        "category": "investment",
        "sub_category": "sukuk",
        "name": "ADIB Sukuk Fund",
        "provider": "Abu Dhabi Islamic Bank",
        "description": "Sharia-compliant fixed income fund investing in quality sukuk instruments.",
        "min_salary": 8000, "min_age": 21, "max_age": 70, "risk_level": "low",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["Sharia compliant", "Stable returns", "Capital preservation", "Monthly income option"],
        "tenure_months": None, "sharia_compliant": True, "rating": 4.0,
        "features": {"min_investment": "AED 5,000", "management_fee": "0.75%", "expected_return": "4-6% p.a.", "risk_rating": "Low"},
    },
    {
        "policy_id": "inv-003",
        "category": "investment",
        "sub_category": "mena_fund",
        "name": "Franklin Templeton MENA Fund",
        "provider": "Franklin Templeton",
        "description": "Actively managed fund focused on high-growth equities across Middle East and North Africa markets.",
        "min_salary": 8000, "min_age": 21, "max_age": 70, "risk_level": "high",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["MENA growth exposure", "Active stock selection", "USD-denominated", "Quarterly dividends", "DFSA regulated"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.2,
        "features": {"min_investment": "USD 5,000", "management_fee": "1.75%", "expected_return": "10-15% p.a.", "risk_rating": "High"},
    },
    {
        "policy_id": "inv-004",
        "category": "investment",
        "sub_category": "reit",
        "name": "Emirates REIT",
        "provider": "Equitativa (Dubai)",
        "description": "Sharia-compliant real estate investment trust listed on Nasdaq Dubai, investing in income-generating UAE properties.",
        "min_salary": 5000, "min_age": 18, "max_age": 70, "risk_level": "medium",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["Sharia compliant", "Listed on Nasdaq Dubai", "Regular dividend distributions", "Diversified property portfolio", "USD denominated"],
        "tenure_months": None, "sharia_compliant": True, "rating": 3.9,
        "features": {"min_investment": "Market price (~USD 0.50/unit)", "management_fee": "1.5%", "expected_return": "6-9% p.a.", "risk_rating": "Medium"},
    },
    {
        "policy_id": "inv-005",
        "category": "investment",
        "sub_category": "robo_advisor",
        "name": "StashAway MENA Portfolio",
        "provider": "StashAway",
        "description": "Algorithm-driven globally diversified investment portfolio, auto-rebalanced based on economic risk index.",
        "min_salary": 3000, "min_age": 18, "max_age": 70, "risk_level": "medium",
        "monthly_cost": None, "annual_cost": None,
        "benefits": ["No minimum investment", "Auto-rebalancing", "Low fees", "DIFC regulated", "Mobile-first platform"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.3,
        "features": {"min_investment": "AED 0", "management_fee": "0.2-0.8%", "expected_return": "6-10% p.a.", "risk_rating": "Customisable"},
    },
    # ── Bank Accounts ──────────────────────────────────────────────────────
    {
        "policy_id": "ba-001",
        "category": "bank_account",
        "sub_category": "savings",
        "name": "RAKBank High Yield Savings",
        "provider": "RAKBank",
        "description": "High-interest savings account with no minimum balance requirement.",
        "min_salary": 3000, "min_age": 18, "max_age": 70, "risk_level": "low",
        "monthly_cost": 0, "annual_cost": 0,
        "benefits": ["No minimum balance", "Free debit card", "Online banking", "ATM access nationwide"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.3,
        "features": {"interest_rate": "3.5% p.a.", "min_balance": "AED 0", "withdrawal_limit": "Unlimited", "card": "Free Visa debit"},
    },
    {
        "policy_id": "ba-002",
        "category": "bank_account",
        "sub_category": "current",
        "name": "CBD Elite Current Account",
        "provider": "Commercial Bank of Dubai",
        "description": "Premium current account with relationship manager and exclusive banking benefits.",
        "min_salary": 20000, "min_age": 21, "max_age": 70, "risk_level": "low",
        "monthly_cost": 0, "annual_cost": 0,
        "benefits": ["Dedicated relationship manager", "Priority banking", "Free international transfers", "Premium debit card"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.4,
        "features": {"min_balance": "AED 100,000", "international_transfers": "Free", "card": "Visa Infinite debit", "lounge_access": "4 visits/year"},
    },
    {
        "policy_id": "ba-003",
        "category": "bank_account",
        "sub_category": "islamic_savings",
        "name": "FAB Islamic Savings Account",
        "provider": "First Abu Dhabi Bank",
        "description": "Sharia-compliant savings account with profit sharing, no monthly fees and flexible access.",
        "min_salary": 3000, "min_age": 18, "max_age": 70, "risk_level": "low",
        "monthly_cost": 0, "annual_cost": 0,
        "benefits": ["Sharia compliant", "Profit sharing quarterly", "No monthly fees", "Free debit card", "Zakat calculation tool"],
        "tenure_months": None, "sharia_compliant": True, "rating": 4.2,
        "features": {"profit_rate": "2.5% p.a.", "min_balance": "AED 3,000", "card": "Free Visa debit", "withdrawal_limit": "Unlimited"},
    },
    {
        "policy_id": "ba-004",
        "category": "bank_account",
        "sub_category": "digital",
        "name": "Mashreq Neo Digital Account",
        "provider": "Mashreq Bank",
        "description": "100% digital bank account opened in minutes on your phone with no paperwork, free transfers and zero monthly fees.",
        "min_salary": 0, "min_age": 18, "max_age": 70, "risk_level": "low",
        "monthly_cost": 0, "annual_cost": 0,
        "benefits": ["Open in minutes online", "Zero monthly fees", "Free local transfers", "Virtual card instant", "Budgeting tools"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.5,
        "features": {"interest_rate": "2% p.a.", "min_balance": "AED 0", "card": "Virtual + Physical Visa", "transfers": "Free unlimited"},
    },
    {
        "policy_id": "ba-005",
        "category": "bank_account",
        "sub_category": "youth",
        "name": "Emirates NBD Youth Account",
        "provider": "Emirates NBD",
        "description": "Dedicated account for UAE residents aged 18-30 with cashback on everyday spend, free remittances and savings goals.",
        "min_salary": 0, "min_age": 18, "max_age": 30, "risk_level": "low",
        "monthly_cost": 0, "annual_cost": 0,
        "benefits": ["Zero fees for under 30s", "2% cashback on dining & entertainment", "Free international remittances (2/month)", "Savings goal tracker", "Instant card"],
        "tenure_months": None, "sharia_compliant": False, "rating": 4.3,
        "features": {"interest_rate": "1.5% p.a.", "min_balance": "AED 0", "card": "Free Visa debit", "remittances": "2 free/month"},
    },
]

# ── Main ───────────────────────────────────────────────────────────────────

async def main():
    force = "--force" in sys.argv

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    try:
        count = await db.policies.count_documents({})
        if count > 0 and not force:
            print(f"Collection already has {count} documents. Use --force to drop and re-seed.")
            return

        if count > 0:
            await db.policies.drop()
            print(f"Dropped existing policies collection ({count} documents).")

        await db.policies.create_index("policy_id", unique=True)
        result = await db.policies.insert_many(FINANCIAL_POLICIES)
        print(f"Inserted {len(result.inserted_ids)} policies into '{DB_NAME}.policies'.")

        by_category: dict = {}
        for p in FINANCIAL_POLICIES:
            by_category.setdefault(p["category"], 0)
            by_category[p["category"]] += 1
        for cat, n in sorted(by_category.items()):
            print(f"  {cat}: {n}")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())

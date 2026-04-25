import os
import json
import uuid
import random
import string
import asyncio
import re
from urllib.parse import quote_plus, unquote, urlparse, urlunparse
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
import httpx

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from passlib.context import CryptContext
from jose import JWTError, jwt

# ─── Config ────────────────────────────────────────────────

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "").strip()
NEWS_API_URL = "https://eventregistry.org/api/v1/article/getArticles"
NEWS_CACHE_TTL = 1800  # 30 minutes

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

_raw_mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
MONGO_URL = _encode_mongo_url(_raw_mongo_url)
# Debug: log masked URL to confirm parsing (remove after fix)
_scheme_match = re.match(r'^(mongodb(?:\+srv)?://)', MONGO_URL)
if _scheme_match:
    _rest = MONGO_URL[len(_scheme_match.group(1)):]
    _at = _rest.rfind('@')
    _colon = _rest.find(':')
    _user = _rest[:_colon] if _colon != -1 else '?'
    _host = _rest[_at+1:] if _at != -1 else '?'
    print(f"[DEBUG] MONGO_URL parsed — user={_user!r} host={_host!r} raw_len={len(_raw_mongo_url)}", flush=True)
DB_NAME = os.environ.get("DB_NAME", "finae")
JWT_SECRET = os.environ.get("JWT_SECRET", "finae-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

# ─── In-Memory Store (non-persistent: news, AI sessions) ──

news_store: list = []
conversations_store: dict = {}
profiles_store: dict = {}
open_chats_store: dict = {}

_news_cache: dict = {"articles": [], "fetched_at": None}

CATEGORY_IMAGE_MAP = {
    "monetary_policy": "dubai_skyline_news_1",
    "real_estate": "dubai_skyline_news_2",
    "investment": "investment_chart",
    "banking": "credit_card_mockup",
    "insurance": "arabic_business",
    "lending": "lending_finance",
}

# ─── Database ──────────────────────────────────────────────

db_client: AsyncIOMotorClient = None
db = None

POLICY_COLLECTION_BY_CATEGORY = {
    "insurance": "policies_insurance",
    "loan": "policies_loans",
    "credit_card": "policies_credit_cards",
    "investment": "policies_investments",
    "bank_account": "policies_bank_accounts",
}
POLICY_SPLIT_COLLECTIONS = list(POLICY_COLLECTION_BY_CATEGORY.values())
LEGACY_POLICY_COLLECTION = "policies"

POLICY_CATEGORY_NORMALIZATION = {
    "credit card": "credit_card",
    "credit cards": "credit_card",
    "credit-card": "credit_card",
    "bank account": "bank_account",
    "bank accounts": "bank_account",
    "bank-account": "bank_account",
    "investments": "investment",
    "loans": "loan",
}

POLICY_ID_PREFIX_TO_CATEGORY = (
    ("ins-", "insurance"),
    ("loan-", "loan"),
    ("cc-", "credit_card"),
    ("inv-", "investment"),
    ("ba-", "bank_account"),
)


def normalize_policy_category(raw_category: Optional[str]) -> Optional[str]:
    if not raw_category:
        return None
    key = raw_category.strip().lower().replace("-", "_")
    return POLICY_CATEGORY_NORMALIZATION.get(key, key)


def infer_category_from_policy_id(policy_id: str) -> Optional[str]:
    pid = (policy_id or "").strip().lower()
    for prefix, category in POLICY_ID_PREFIX_TO_CATEGORY:
        if pid.startswith(prefix):
            return category
    return None


def policy_query_collections(category: Optional[str] = None) -> list:
    normalized = normalize_policy_category(category)
    if normalized and normalized in POLICY_COLLECTION_BY_CATEGORY:
        return [
            db[POLICY_COLLECTION_BY_CATEGORY[normalized]],
            db[LEGACY_POLICY_COLLECTION],
        ]
    return [*(db[name] for name in POLICY_SPLIT_COLLECTIONS), db[LEGACY_POLICY_COLLECTION]]

# ─── Auth Helpers ──────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def generate_app_number() -> str:
    date_part = datetime.now().strftime("%Y%m%d")
    rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"FIN-{date_part}-{rand_part}"


# ─── Lifespan ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, db
    db_client = AsyncIOMotorClient(MONGO_URL)
    db = db_client[DB_NAME]
    await db.users.create_index("email", unique=True)
    await db.applications.create_index("user_id")
    await db.applications.create_index("application_number", unique=True)
    for collection_name in POLICY_SPLIT_COLLECTIONS:
        await db[collection_name].create_index("policy_id", unique=True)
    await db.policies.create_index("policy_id", unique=True)
    await seed_data()
    yield
    db_client.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic Models ──────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class OpenChatRequest(BaseModel):
    session_id: str
    message: str

class ExtractProfileRequest(BaseModel):
    session_id: str

class RecommendRequest(BaseModel):
    session_id: str
    category: Optional[str] = None

class CompareRequest(BaseModel):
    policy_ids: list[str]

class ApplicationRequest(BaseModel):
    session_id: Optional[str] = None
    policy_id: str
    user_profile: dict

class ApplicationUpdateRequest(BaseModel):
    status: str

class AgentActionRequest(BaseModel):
    session_id: str
    action_type: str
    action_data: dict

# ─── Seed Data ─────────────────────────────────────────────

FINANCIAL_POLICIES = [
    # ── Insurance ──────────────────────────────────────────────
    {
        "policy_id": "ins-001",
        "category": "insurance",
        "sub_category": "health",
        "name": "ADNIC Premium Health Cover",
        "provider": "Abu Dhabi National Insurance Company",
        "description": "Comprehensive health insurance with worldwide coverage, dental, optical, and maternity benefits.",
        "min_salary": 8000,
        "min_age": 18,
        "max_age": 65,
        "risk_level": "low",
        "monthly_cost": 450,
        "annual_cost": 5000,
        "benefits": ["Worldwide coverage", "Dental & optical", "Maternity benefits", "No claim bonus", "Wellness programs"],
        "tenure_months": 12,
        "sharia_compliant": False,
        "rating": 4.5,
        "features": {"coverage_limit": "AED 1,000,000", "deductible": "AED 500", "network": "300+ hospitals"}
    },
    {
        "policy_id": "ins-002",
        "category": "insurance",
        "sub_category": "health",
        "name": "Takaful Emarat Family Shield",
        "provider": "Takaful Emarat",
        "description": "Sharia-compliant family health insurance with comprehensive inpatient and outpatient coverage.",
        "min_salary": 5000,
        "min_age": 21,
        "max_age": 60,
        "risk_level": "low",
        "monthly_cost": 350,
        "annual_cost": 3800,
        "benefits": ["Sharia compliant", "Family coverage", "Outpatient care", "Prescription drugs", "Annual health check"],
        "tenure_months": 12,
        "sharia_compliant": True,
        "rating": 4.3,
        "features": {"coverage_limit": "AED 500,000", "deductible": "AED 200", "network": "200+ hospitals"}
    },
    {
        "policy_id": "ins-003",
        "category": "insurance",
        "sub_category": "life",
        "name": "MetLife SecureLife Plan",
        "provider": "MetLife UAE",
        "description": "Term life insurance with critical illness cover and accidental death benefit.",
        "min_salary": 10000,
        "min_age": 25,
        "max_age": 55,
        "risk_level": "low",
        "monthly_cost": 200,
        "annual_cost": 2200,
        "benefits": ["Critical illness cover", "Accidental death benefit", "Premium waiver", "Repatriation cover"],
        "tenure_months": 120,
        "sharia_compliant": False,
        "rating": 4.6,
        "features": {"coverage_limit": "AED 2,000,000", "premium_term": "10 years", "payout": "Lump sum"}
    },
    {
        "policy_id": "loan-001",
        "category": "loan",
        "sub_category": "personal",
        "name": "Emirates NBD Personal Loan",
        "provider": "Emirates NBD",
        "description": "Competitive personal loan with salary transfer, up to AED 3 million with flexible tenure.",
        "min_salary": 5000,
        "min_age": 21,
        "max_age": 60,
        "risk_level": "medium",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["Up to AED 3M", "Flexible tenure 12-48 months", "Quick approval", "No guarantor needed"],
        "tenure_months": 48,
        "sharia_compliant": False,
        "rating": 4.4,
        "features": {"interest_rate": "3.99% flat", "max_amount": "AED 3,000,000", "processing_fee": "1%", "min_tenure": "12 months"}
    },
    {
        "policy_id": "loan-002",
        "category": "loan",
        "sub_category": "personal",
        "name": "Dubai Islamic Bank Personal Finance",
        "provider": "Dubai Islamic Bank",
        "description": "Sharia-compliant personal finance with competitive profit rates and salary transfer benefit.",
        "min_salary": 5000,
        "min_age": 21,
        "max_age": 60,
        "risk_level": "medium",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["Sharia compliant", "Up to AED 2.5M", "Salary transfer benefit", "Life Takaful included"],
        "tenure_months": 48,
        "sharia_compliant": True,
        "rating": 4.3,
        "features": {"profit_rate": "4.25% flat", "max_amount": "AED 2,500,000", "processing_fee": "1.05%", "min_tenure": "12 months"}
    },
    {
        "policy_id": "loan-003",
        "category": "loan",
        "sub_category": "home",
        "name": "HSBC Home Mortgage",
        "provider": "HSBC UAE",
        "description": "Home mortgage for UAE residents with competitive rates and up to 80% financing.",
        "min_salary": 15000,
        "min_age": 25,
        "max_age": 60,
        "risk_level": "medium",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["Up to 80% financing", "Fixed rate options", "Property valuation included", "Free property insurance year 1"],
        "tenure_months": 300,
        "sharia_compliant": False,
        "rating": 4.5,
        "features": {"interest_rate": "3.49% variable", "max_amount": "AED 15,000,000", "ltv": "80%", "min_tenure": "60 months"}
    },
    {
        "policy_id": "cc-001",
        "category": "credit_card",
        "sub_category": "rewards",
        "name": "FAB Rewards World Elite Mastercard",
        "provider": "First Abu Dhabi Bank",
        "description": "Premium rewards credit card with airport lounge access and travel benefits.",
        "min_salary": 15000,
        "min_age": 21,
        "max_age": 65,
        "risk_level": "low",
        "monthly_cost": None,
        "annual_cost": 500,
        "benefits": ["Unlimited lounge access", "3x reward points on travel", "Free travel insurance", "Concierge service"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.7,
        "features": {"annual_fee": "AED 500", "reward_rate": "3x on travel", "credit_limit": "Up to AED 500,000", "cashback": "1%"}
    },
    {
        "policy_id": "cc-002",
        "category": "credit_card",
        "sub_category": "cashback",
        "name": "Mashreq Cashback Card",
        "provider": "Mashreq Bank",
        "description": "Everyday cashback credit card with no annual fee for the first year.",
        "min_salary": 8000,
        "min_age": 21,
        "max_age": 65,
        "risk_level": "low",
        "monthly_cost": None,
        "annual_cost": 0,
        "benefits": ["5% cashback on dining", "3% on groceries", "1% on everything else", "Free for first year"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.2,
        "features": {"annual_fee": "AED 0 (first year)", "reward_rate": "Up to 5%", "credit_limit": "Up to AED 200,000", "cashback": "5% dining"}
    },
    {
        "policy_id": "inv-001",
        "category": "investment",
        "sub_category": "mutual_fund",
        "name": "Emirates NBD Global Equity Fund",
        "provider": "Emirates NBD Asset Management",
        "description": "Diversified global equity fund targeting long-term capital growth.",
        "min_salary": 10000,
        "min_age": 21,
        "max_age": 70,
        "risk_level": "high",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["Global diversification", "Professional management", "Quarterly reporting", "Online access"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.1,
        "features": {"min_investment": "AED 10,000", "management_fee": "1.5%", "expected_return": "8-12% p.a.", "risk_rating": "High"}
    },
    {
        "policy_id": "inv-002",
        "category": "investment",
        "sub_category": "sukuk",
        "name": "ADIB Sukuk Fund",
        "provider": "Abu Dhabi Islamic Bank",
        "description": "Sharia-compliant fixed income fund investing in quality sukuk instruments.",
        "min_salary": 8000,
        "min_age": 21,
        "max_age": 70,
        "risk_level": "low",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["Sharia compliant", "Stable returns", "Capital preservation", "Monthly income option"],
        "tenure_months": None,
        "sharia_compliant": True,
        "rating": 4.0,
        "features": {"min_investment": "AED 5,000", "management_fee": "0.75%", "expected_return": "4-6% p.a.", "risk_rating": "Low"}
    },
    {
        "policy_id": "ba-001",
        "category": "bank_account",
        "sub_category": "savings",
        "name": "RAKBank High Yield Savings",
        "provider": "RAKBank",
        "description": "High-interest savings account with no minimum balance requirement.",
        "min_salary": 3000,
        "min_age": 18,
        "max_age": 70,
        "risk_level": "low",
        "monthly_cost": 0,
        "annual_cost": 0,
        "benefits": ["No minimum balance", "Free debit card", "Online banking", "ATM access nationwide"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.3,
        "features": {"interest_rate": "3.5% p.a.", "min_balance": "AED 0", "withdrawal_limit": "Unlimited", "card": "Free Visa debit"}
    },
    {
        "policy_id": "ba-002",
        "category": "bank_account",
        "sub_category": "current",
        "name": "CBD Elite Current Account",
        "provider": "Commercial Bank of Dubai",
        "description": "Premium current account with relationship manager and exclusive banking benefits.",
        "min_salary": 20000,
        "min_age": 21,
        "max_age": 70,
        "risk_level": "low",
        "monthly_cost": 0,
        "annual_cost": 0,
        "benefits": ["Dedicated relationship manager", "Priority banking", "Free international transfers", "Premium debit card"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.4,
        "features": {"min_balance": "AED 100,000", "international_transfers": "Free", "card": "Visa Infinite debit", "lounge_access": "4 visits/year"}
    },
    # ── Additional Credit Cards ─────────────────────────────────
    {
        "policy_id": "cc-003",
        "category": "credit_card",
        "sub_category": "travel",
        "name": "Emirates NBD Skywards Signature",
        "provider": "Emirates NBD",
        "description": "Premium travel credit card that earns Skywards Miles on every spend, with airport lounge access and travel insurance.",
        "min_salary": 10000,
        "min_age": 21,
        "max_age": 65,
        "risk_level": "low",
        "monthly_cost": None,
        "annual_cost": 400,
        "benefits": ["3 Skywards Miles per AED spent", "Unlimited lounge access", "Complimentary travel insurance", "Golf privileges", "No foreign transaction fees"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.6,
        "features": {"annual_fee": "AED 400", "reward_rate": "3 miles/AED", "credit_limit": "Up to AED 300,000", "lounge": "Unlimited LoungeKey"}
    },
    {
        "policy_id": "cc-004",
        "category": "credit_card",
        "sub_category": "islamic",
        "name": "DIB Cashback Credit Card",
        "provider": "Dubai Islamic Bank",
        "description": "Sharia-compliant credit card offering cashback on everyday categories with zero interest on monthly repayment.",
        "min_salary": 5000,
        "min_age": 21,
        "max_age": 65,
        "risk_level": "low",
        "monthly_cost": None,
        "annual_cost": 0,
        "benefits": ["Sharia compliant", "5% cashback on fuel", "3% on supermarkets", "2% on utilities", "No annual fee for first year"],
        "tenure_months": None,
        "sharia_compliant": True,
        "rating": 4.1,
        "features": {"annual_fee": "AED 0 (first year)", "reward_rate": "Up to 5% cashback", "credit_limit": "Up to AED 150,000", "cashback_cap": "AED 500/month"}
    },
    {
        "policy_id": "cc-005",
        "category": "credit_card",
        "sub_category": "lifestyle",
        "name": "ADCB SimplyLife Cashback Card",
        "provider": "Abu Dhabi Commercial Bank",
        "description": "Entry-level cashback card with no annual fee, ideal for everyday spending with instant cashback rewards.",
        "min_salary": 5000,
        "min_age": 21,
        "max_age": 65,
        "risk_level": "low",
        "monthly_cost": None,
        "annual_cost": 0,
        "benefits": ["No annual fee", "2% cashback on online shopping", "1% on all other spend", "Contactless payments", "Free supplementary cards"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.0,
        "features": {"annual_fee": "AED 0", "reward_rate": "Up to 2%", "credit_limit": "Up to AED 100,000", "supplementary_cards": "3 free"}
    },
    # ── Additional Insurance ────────────────────────────────────
    {
        "policy_id": "ins-004",
        "category": "insurance",
        "sub_category": "motor",
        "name": "AXA Comprehensive Motor Shield",
        "provider": "AXA Gulf",
        "description": "Comprehensive motor insurance with agency repairs, roadside assistance, and personal accident cover.",
        "min_salary": 3000,
        "min_age": 21,
        "max_age": 65,
        "risk_level": "low",
        "monthly_cost": 200,
        "annual_cost": 2200,
        "benefits": ["Agency repairs", "24/7 roadside assistance", "Personal accident cover", "Hire car while in repair", "GCC coverage"],
        "tenure_months": 12,
        "sharia_compliant": False,
        "rating": 4.4,
        "features": {"coverage_limit": "Third party unlimited", "deductible": "AED 1,000", "gcc_coverage": "Yes", "roadside": "24/7"}
    },
    {
        "policy_id": "ins-005",
        "category": "insurance",
        "sub_category": "travel",
        "name": "Oman Insurance Travel Guard",
        "provider": "Oman Insurance Company",
        "description": "Comprehensive travel insurance covering medical emergencies, trip cancellation, baggage loss and flight delays.",
        "min_salary": 3000,
        "min_age": 18,
        "max_age": 70,
        "risk_level": "low",
        "monthly_cost": None,
        "annual_cost": 500,
        "benefits": ["Medical cover up to USD 1M", "Trip cancellation", "Baggage loss", "Flight delay compensation", "Adventure sports rider available"],
        "tenure_months": 12,
        "sharia_compliant": False,
        "rating": 4.2,
        "features": {"medical_cover": "USD 1,000,000", "cancellation": "Up to AED 10,000", "baggage": "Up to AED 5,000", "family_plan": "Available"}
    },
    {
        "policy_id": "ins-006",
        "category": "insurance",
        "sub_category": "home",
        "name": "RSA Home Protect Plus",
        "provider": "RSA Insurance",
        "description": "All-risks home contents and building insurance protecting against fire, theft, flood and accidental damage.",
        "min_salary": 5000,
        "min_age": 18,
        "max_age": 70,
        "risk_level": "low",
        "monthly_cost": 80,
        "annual_cost": 900,
        "benefits": ["Building & contents cover", "Theft & burglary", "Accidental damage", "Domestic helper cover", "Alternative accommodation"],
        "tenure_months": 12,
        "sharia_compliant": False,
        "rating": 4.1,
        "features": {"building_limit": "AED 3,000,000", "contents_limit": "AED 500,000", "deductible": "AED 500", "helper_cover": "Up to AED 50,000"}
    },
    # ── Additional Loans ────────────────────────────────────────
    {
        "policy_id": "loan-004",
        "category": "loan",
        "sub_category": "personal",
        "name": "ADCB TouchPoints Personal Loan",
        "provider": "Abu Dhabi Commercial Bank",
        "description": "Personal loan with TouchPoints rewards on every repayment, quick disbursement and flexible tenure.",
        "min_salary": 8000,
        "min_age": 21,
        "max_age": 60,
        "risk_level": "medium",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["TouchPoints on repayments", "Same-day approval", "Up to AED 1.5M", "No early settlement fee after 12 months"],
        "tenure_months": 48,
        "sharia_compliant": False,
        "rating": 4.3,
        "features": {"interest_rate": "4.49% flat", "max_amount": "AED 1,500,000", "processing_fee": "1%", "early_settlement": "Free after 12 months"}
    },
    {
        "policy_id": "loan-005",
        "category": "loan",
        "sub_category": "personal",
        "name": "Mashreq Salary Transfer Loan",
        "provider": "Mashreq Bank",
        "description": "Competitive personal loan exclusively for salary transfer customers with preferential rates and instant approval.",
        "min_salary": 5000,
        "min_age": 21,
        "max_age": 60,
        "risk_level": "medium",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["Preferential salary transfer rate", "Instant online approval", "Up to AED 1M", "Free life insurance", "Zero processing fee"],
        "tenure_months": 48,
        "sharia_compliant": False,
        "rating": 4.2,
        "features": {"interest_rate": "3.75% flat", "max_amount": "AED 1,000,000", "processing_fee": "0%", "insurance": "Free life cover"}
    },
    {
        "policy_id": "loan-006",
        "category": "loan",
        "sub_category": "auto",
        "name": "FAB Auto Finance",
        "provider": "First Abu Dhabi Bank",
        "description": "New and used car finance with up to 80% LTV, competitive rates and quick approval for UAE residents.",
        "min_salary": 7000,
        "min_age": 21,
        "max_age": 60,
        "risk_level": "medium",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["Up to 80% vehicle value", "New & used cars", "Flexible 12–60 month tenure", "Insurance bundling option"],
        "tenure_months": 60,
        "sharia_compliant": False,
        "rating": 4.3,
        "features": {"interest_rate": "3.25% flat", "max_amount": "AED 1,000,000", "ltv": "80%", "processing_fee": "1%"}
    },
    # ── Additional Investments ──────────────────────────────────
    {
        "policy_id": "inv-003",
        "category": "investment",
        "sub_category": "mena_fund",
        "name": "Franklin Templeton MENA Fund",
        "provider": "Franklin Templeton",
        "description": "Actively managed fund focused on high-growth equities across Middle East and North Africa markets.",
        "min_salary": 8000,
        "min_age": 21,
        "max_age": 70,
        "risk_level": "high",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["MENA growth exposure", "Active stock selection", "USD-denominated", "Quarterly dividends", "DFSA regulated"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.2,
        "features": {"min_investment": "USD 5,000", "management_fee": "1.75%", "expected_return": "10-15% p.a.", "risk_rating": "High"}
    },
    {
        "policy_id": "inv-004",
        "category": "investment",
        "sub_category": "reit",
        "name": "Emirates REIT",
        "provider": "Equitativa (Dubai)",
        "description": "Sharia-compliant real estate investment trust listed on Nasdaq Dubai, investing in income-generating UAE properties.",
        "min_salary": 5000,
        "min_age": 18,
        "max_age": 70,
        "risk_level": "medium",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["Sharia compliant", "Listed on Nasdaq Dubai", "Regular dividend distributions", "Diversified property portfolio", "USD denominated"],
        "tenure_months": None,
        "sharia_compliant": True,
        "rating": 3.9,
        "features": {"min_investment": "Market price (~USD 0.50/unit)", "management_fee": "1.5%", "expected_return": "6-9% p.a.", "risk_rating": "Medium"}
    },
    {
        "policy_id": "inv-005",
        "category": "investment",
        "sub_category": "robo_advisor",
        "name": "StashAway MENA Portfolio",
        "provider": "StashAway",
        "description": "Algorithm-driven globally diversified investment portfolio, auto-rebalanced based on economic risk index.",
        "min_salary": 3000,
        "min_age": 18,
        "max_age": 70,
        "risk_level": "medium",
        "monthly_cost": None,
        "annual_cost": None,
        "benefits": ["No minimum investment", "Auto-rebalancing", "Low fees", "DIFC regulated", "Mobile-first platform"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.3,
        "features": {"min_investment": "AED 0", "management_fee": "0.2–0.8%", "expected_return": "6-10% p.a.", "risk_rating": "Customisable"}
    },
    # ── Additional Bank Accounts ────────────────────────────────
    {
        "policy_id": "ba-003",
        "category": "bank_account",
        "sub_category": "islamic_savings",
        "name": "FAB Islamic Savings Account",
        "provider": "First Abu Dhabi Bank",
        "description": "Sharia-compliant savings account with profit sharing, no monthly fees and flexible access.",
        "min_salary": 3000,
        "min_age": 18,
        "max_age": 70,
        "risk_level": "low",
        "monthly_cost": 0,
        "annual_cost": 0,
        "benefits": ["Sharia compliant", "Profit sharing quarterly", "No monthly fees", "Free debit card", "Zakat calculation tool"],
        "tenure_months": None,
        "sharia_compliant": True,
        "rating": 4.2,
        "features": {"profit_rate": "2.5% p.a.", "min_balance": "AED 3,000", "card": "Free Visa debit", "withdrawal_limit": "Unlimited"}
    },
    {
        "policy_id": "ba-004",
        "category": "bank_account",
        "sub_category": "digital",
        "name": "Mashreq Neo Digital Account",
        "provider": "Mashreq Bank",
        "description": "100% digital bank account opened in minutes on your phone with no paperwork, free transfers and zero monthly fees.",
        "min_salary": 0,
        "min_age": 18,
        "max_age": 70,
        "risk_level": "low",
        "monthly_cost": 0,
        "annual_cost": 0,
        "benefits": ["Open in minutes online", "Zero monthly fees", "Free local transfers", "Virtual card instant", "Budgeting tools"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.5,
        "features": {"interest_rate": "2% p.a.", "min_balance": "AED 0", "card": "Virtual + Physical Visa", "transfers": "Free unlimited"}
    },
    {
        "policy_id": "ba-005",
        "category": "bank_account",
        "sub_category": "youth",
        "name": "Emirates NBD Youth Account",
        "provider": "Emirates NBD",
        "description": "Dedicated account for UAE residents aged 18-30 with cashback on everyday spend, free remittances and savings goals.",
        "min_salary": 0,
        "min_age": 18,
        "max_age": 30,
        "risk_level": "low",
        "monthly_cost": 0,
        "annual_cost": 0,
        "benefits": ["Zero fees for under 30s", "2% cashback on dining & entertainment", "Free international remittances (2/month)", "Savings goal tracker", "Instant card"],
        "tenure_months": None,
        "sharia_compliant": False,
        "rating": 4.3,
        "features": {"interest_rate": "1.5% p.a.", "min_balance": "AED 0", "card": "Free Visa debit", "remittances": "2 free/month"}
    },
]

FINANCIAL_NEWS = [
    {
        "news_id": "news-001",
        "title": "UAE Central Bank Holds Interest Rate Steady at 4.5%",
        "summary": "The UAE Central Bank maintained its base rate at 4.5%, following the US Federal Reserve's decision. Analysts expect this stability to support lending and mortgage markets in H1 2026.",
        "category": "monetary_policy",
        "date": "2026-01-14",
        "source": "Gulf News",
        "image_key": "dubai_skyline_news_1",
        "impact": "Positive for borrowers. Fixed-rate products remain attractive."
    },
    {
        "news_id": "news-002",
        "title": "Dubai Real Estate Hits Record AED 500B in 2025 Transactions",
        "summary": "Dubai's property market achieved record transaction volumes in 2025, driven by foreign investor demand and new golden visa regulations.",
        "category": "real_estate",
        "date": "2026-01-12",
        "source": "Arabian Business",
        "image_key": "dubai_skyline_news_2",
        "impact": "Home loan demand expected to rise. Compare mortgage rates now."
    },
    {
        "news_id": "news-003",
        "title": "New Sharia-Compliant Investment Products Launch in Abu Dhabi",
        "summary": "ADGM announces new regulatory framework enabling innovative sukuk and Islamic fintech products, expanding options for Sharia-conscious investors.",
        "category": "investment",
        "date": "2026-01-10",
        "source": "The National",
        "image_key": "investment_chart",
        "impact": "More choice for Sharia-compliant investing. Review your portfolio allocation."
    },
    {
        "news_id": "news-004",
        "title": "Credit Card Spending in UAE Grows 18% Year-on-Year",
        "summary": "Card spending surged driven by digital payments adoption and reward program enhancements by major banks.",
        "category": "banking",
        "date": "2026-01-08",
        "source": "Khaleej Times",
        "image_key": "arabic_business",
        "impact": "Maximize rewards by switching to higher-cashback cards."
    },
    {
        "news_id": "news-005",
        "title": "UAE Insurance Sector Posts 12% Premium Growth",
        "summary": "Health and motor insurance led growth as new mandatory coverage requirements and population expansion drive demand.",
        "category": "insurance",
        "date": "2026-01-06",
        "source": "Insurance Business ME",
        "image_key": "arabic_business",
        "impact": "Review your health cover. New entrants mean more competitive premiums."
    },
    {
        "news_id": "news-006",
        "title": "Personal Loan Interest Rates Drop to 3-Year Low",
        "summary": "Competition among UAE banks has driven personal loan flat rates below 4% for salary transfer customers, offering significant savings.",
        "category": "lending",
        "date": "2026-01-04",
        "source": "Gulf News",
        "image_key": "lending_finance",
        "impact": "Excellent time to consolidate debt or finance major purchases."
    }
]

async def seed_data():
    global news_store
    news_store = list(FINANCIAL_NEWS)

    total_seeded = 0
    for category, collection_name in POLICY_COLLECTION_BY_CATEGORY.items():
        collection = db[collection_name]
        count = await collection.count_documents({})
        if count == 0:
            docs = [dict(p) for p in FINANCIAL_POLICIES if p.get("category") == category]
            if docs:
                await collection.insert_many(docs)
                total_seeded += len(docs)
                print(f"Seeded {len(docs)} policies into {collection_name}")
        else:
            print(f"{collection_name} already has {count} documents — skipping seed")

    if total_seeded:
        print(f"Total seeded policies: {total_seeded}")

    print(f"Loaded {len(news_store)} static news articles")

# ─── Helper: Call Groq ─────────────────────────────────────

def call_groq(messages: list, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")

AVATAR_SYSTEM_PROMPT = """You are Fin-ae, a friendly and professional AI financial assistant for the UAE market. You help users find the best financial products including insurance, loans, credit cards, investments, and bank accounts.

**Personality**
- Professional yet warm and approachable
- Knowledgeable about UAE financial products and regulations
- Use **markdown formatting** in every response: bold key terms, bullet lists for options, numbered steps where relevant
- Never provide regulated financial advice — always suggest consulting a licensed advisor for final decisions

## Information Gathering — Strict Rules

You must collect the following pieces of information **one question at a time**, in order. Do NOT combine multiple questions into a single message. Do NOT move to the next question until the current one is answered.

**Required information (collect in this exact order):**
1. Product category (insurance / loan / credit card / investment / bank account)
2. Full name
3. Age (in years)
4. Nationality
5. UAE residency status (resident / visitor / citizen)
6. Monthly income in AED
7. Employment type (salaried / self-employed / business owner)
8. Risk appetite (conservative / moderate / aggressive)
9. Sharia-compliant preference (yes / no)
10. Any specific requirements or concerns

**Follow-up rule:** If the user's reply does not answer the current question (e.g. they gave their name but not their age), politely ask for the missing information before advancing. Never silently skip a field.

**Completion:** Once all 10 fields are collected, summarise the profile and say you are finding the best matching products:
> "Based on what you've shared, I have everything I need. Let me find the best **[product type]** options for you..."

## Formatting Rules
- Use **bold** for product names, key figures, and important terms
- Use `-` bullet lists for options or benefits
- Keep each response to 2–4 sentences — never a wall of text
- **Never ask more than one question per message**

## Critical Rules
- Never repeat a question the user has already answered
- Track all provided information across the conversation carefully
- When the user asks about a specific product or policy mentioned, give a concise factual summary"""

EXTRACTION_SYSTEM_PROMPT = """You are a data extraction assistant. Given a conversation between a user and a financial assistant, extract the user's profile information into a structured JSON format.

Return ONLY valid JSON with these fields (use null for missing info):
{
  "name": "string or null",
  "age": "number or null",
  "nationality": "string or null",
  "residency_status": "string or null (UAE resident/visitor/citizen)",
  "monthly_salary": "number or null (in AED)",
  "employment_type": "string or null (salaried/self-employed/business)",
  "financial_goal": "string or null (insurance/loan/investment/credit_card/bank_account)",
  "risk_appetite": "string or null (conservative/moderate/aggressive)",
  "sharia_compliant": "boolean or null",
  "specific_requirements": "string or null",
  "completeness_score": "number 0-100 indicating how complete the profile is"
}

Only return the JSON object, no other text."""

RECOMMENDATION_SYSTEM_PROMPT = """You are a financial product recommendation expert for the UAE market. Given a user profile and a list of matching financial policies, provide clear and concise recommendations.

For each recommended policy:
1. Explain WHY it matches the user's needs (1-2 sentences)
2. Highlight the key benefit most relevant to them
3. Note any considerations

Keep responses professional and concise. Never provide regulated financial advice. Format your response clearly with numbered recommendations."""

# ─── Live News Fetcher ─────────────────────────────────────

async def fetch_live_news() -> list:
    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(
            NEWS_API_URL,
            json={
                "action": "getArticles",
                "keyword": [
                    "UAE banking", "UAE finance", "UAE insurance",
                    "UAE investment", "UAE mortgage", "UAE loan",
                    "Dubai real estate", "Abu Dhabi economy",
                    "UAE interest rate", "UAE central bank"
                ],
                "keywordOper": "OR",
                "keywordLoc": "body,title",
                "lang": "eng",
                "articlesPage": 1,
                "articlesCount": 10,
                "articlesSortBy": "date",
                "articlesSortByAsc": False,
                "resultType": "articles",
                "dataType": ["news"],
                "forceMaxDataTimeWindow": 14,
                "apiKey": NEWS_API_KEY,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    raw_articles = data.get("articles", {}).get("results", [])
    if not raw_articles:
        print("[News] EventRegistry returned 0 articles")
        return []

    print(f"[News] Fetched {len(raw_articles)} raw articles from EventRegistry")

    # Use up to 6 articles with non-empty bodies
    usable = [a for a in raw_articles if (a.get("body") or a.get("title"))][:6]

    articles_text = "\n".join([
        f"{i+1}. Title: {a.get('title', '')}\nBody: {(a.get('body') or '')[:400]}"
        for i, a in enumerate(usable)
    ])

    groq_messages = [
        {
            "role": "system",
            "content": (
                "You are a UAE financial news analyst. For each numbered article return a JSON array "
                "where each element has:\n"
                '- "index": 1-based integer\n'
                '- "category": one of monetary_policy, real_estate, investment, banking, insurance, lending\n'
                '- "summary": two-sentence plain-text summary focused on the key financial takeaway\n'
                '- "impact": one actionable sentence for UAE consumers (max 15 words)\n'
                "Return ONLY a valid JSON array, no markdown fences, no extra text."
            ),
        },
        {"role": "user", "content": f"Analyse these articles:\n\n{articles_text}"},
    ]

    enrichment_map: dict = {}
    try:
        raw = await asyncio.to_thread(call_groq, groq_messages, 0.2, 1200)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned).rstrip("`").strip()
        enriched = json.loads(cleaned)
        if isinstance(enriched, list):
            enrichment_map = {item["index"]: item for item in enriched}
        print(f"[News] Groq enriched {len(enrichment_map)} articles")
    except Exception as e:
        print(f"[News] Groq enrichment error: {e}")

    news_items = []
    for i, article in enumerate(usable):
        enr = enrichment_map.get(i + 1, {})
        category = enr.get("category", "banking")
        date_str = (article.get("dateTime") or "")[:10] or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        body = (article.get("body") or "")
        url = article.get("url", "")
        news_items.append({
            "news_id": f"live-{i + 1}",
            "title": article.get("title", ""),
            "summary": enr.get("summary") or (body[:250] + "..." if len(body) > 250 else body),
            "category": category,
            "date": date_str,
            "source": (article.get("source") or {}).get("title", "News Source"),
            "url": url,
            "image_key": CATEGORY_IMAGE_MAP.get(category, "dubai_skyline_news_1"),
            "impact": enr.get("impact", ""),
            "is_live": True,
        })

    print(f"[News] Returning {len(news_items)} enriched live articles")
    return news_items

# ─── API Routes ────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "finae-api"}

# ── Auth ───────────────────────────────────────────────────

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    if not req.email or not req.password or not req.name:
        raise HTTPException(status_code=400, detail="Email, password and name are required")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = await db.users.find_one({"email": req.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "email": req.email.lower(),
        "name": req.name.strip(),
        "password_hash": hash_password(req.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    token = create_token(user_id, req.email.lower())
    return {
        "token": token,
        "user": {"id": user_id, "email": req.email.lower(), "name": req.name.strip()},
    }


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = await db.users.find_one({"email": req.email.lower()})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_token(user_id, req.email.lower())
    return {
        "token": token,
        "user": {"id": user_id, "email": user["email"], "name": user["name"]},
    }


@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": {"id": str(user["_id"]), "email": user["email"], "name": user["name"]}}

# ── Chat: Avatar Conversation ──────────────────────────────

@app.post("/api/chat/message")
async def chat_message(req: ChatMessageRequest):
    if req.session_id not in conversations_store:
        conversations_store[req.session_id] = {
            "session_id": req.session_id,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    conversation = conversations_store[req.session_id]

    groq_messages = [{"role": "system", "content": AVATAR_SYSTEM_PROMPT}]
    for msg in conversation["messages"]:
        groq_messages.append({"role": msg["role"], "content": msg["content"]})
    groq_messages.append({"role": "user", "content": req.message})

    ai_response = call_groq(groq_messages)

    now = datetime.now(timezone.utc).isoformat()
    conversation["messages"].append({"role": "user", "content": req.message, "timestamp": now})
    conversation["messages"].append({"role": "assistant", "content": ai_response, "timestamp": now})

    return {"response": ai_response, "session_id": req.session_id}

# ── Chat: Extract User Profile ─────────────────────────────

@app.post("/api/chat/extract-profile")
async def extract_profile(req: ExtractProfileRequest):
    conversation = conversations_store.get(req.session_id)

    if not conversation or not conversation.get("messages"):
        raise HTTPException(status_code=404, detail="No conversation found")

    conv_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in conversation["messages"]
    ])

    groq_messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Extract the user profile from this conversation:\n\n{conv_text}"}
    ]

    raw_response = call_groq(groq_messages, temperature=0.1)

    try:
        json_str = raw_response.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        profile = json.loads(json_str.strip())
    except json.JSONDecodeError:
        profile = {"raw_response": raw_response, "completeness_score": 0}

    profiles_store[req.session_id] = {
        "session_id": req.session_id,
        "profile": profile,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    return {"profile": profile, "session_id": req.session_id}

# ── Policies ───────────────────────────────────────────────

def _serialize_policy(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


async def _find_policies(
    query: dict,
    category: Optional[str] = None,
    sort_by_rating: bool = False,
) -> list[dict]:
    policies: list[dict] = []
    seen_ids = set()

    for collection in policy_query_collections(category):
        cursor = collection.find(query)
        async for doc in cursor:
            policy = _serialize_policy(doc)
            policy_id = policy.get("policy_id")
            if policy_id and policy_id in seen_ids:
                continue
            if policy_id:
                seen_ids.add(policy_id)
            policies.append(policy)

    if sort_by_rating:
        policies.sort(key=lambda p: p.get("rating") or 0, reverse=True)

    return policies


async def _find_policy_by_id(policy_id: str) -> Optional[dict]:
    inferred_category = infer_category_from_policy_id(policy_id)
    for collection in policy_query_collections(inferred_category):
        doc = await collection.find_one({"policy_id": policy_id})
        if doc:
            return _serialize_policy(doc)
    return None


@app.get("/api/policies")
async def get_policies(
    category: Optional[str] = Query(None),
    sharia_compliant: Optional[bool] = Query(None),
    min_salary: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
):
    normalized_category = normalize_policy_category(category)

    query: dict = {}
    if normalized_category:
        query["category"] = normalized_category
    if sharia_compliant is not None:
        query["sharia_compliant"] = sharia_compliant
    if risk_level:
        query["risk_level"] = risk_level
    if min_salary:
        query["min_salary"] = {"$lte": min_salary}

    policies = await _find_policies(query, normalized_category)
    return {"policies": policies, "count": len(policies)}


@app.get("/api/policies/{policy_id}")
async def get_policy(policy_id: str):
    policy = await _find_policy_by_id(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policy": policy}

# ── Recommendations ────────────────────────────────────────

@app.post("/api/policies/recommend")
async def recommend_policies(req: RecommendRequest):
    profile_doc = profiles_store.get(req.session_id)

    if not profile_doc:
        raise HTTPException(status_code=404, detail="No profile found. Please complete the avatar conversation first.")

    profile = profile_doc.get("profile", {})

    goal_map = {
        "insurance": "insurance",
        "loan": "loan",
        "investment": "investment",
        "credit_card": "credit_card",
        "bank_account": "bank_account",
        "credit card": "credit_card",
        "bank account": "bank_account",
        "investments": "investment",
        "credit cards": "credit_card",
        "bank accounts": "bank_account",
        "loans": "loan",
    }

    query: dict = {}
    requested_category = normalize_policy_category(req.category)
    if requested_category:
        query["category"] = requested_category
    elif profile.get("financial_goal"):
        mapped = goal_map.get(profile["financial_goal"].lower())
        if mapped:
            query["category"] = mapped

    if profile.get("sharia_compliant"):
        query["sharia_compliant"] = True

    salary = profile.get("monthly_salary")
    if salary:
        query["min_salary"] = {"$lte": salary}

    age = profile.get("age")
    if age:
        query["min_age"] = {"$lte": age}
        query["max_age"] = {"$gte": age}

    policies = await _find_policies(query, query.get("category"), sort_by_rating=True)

    if not policies:
        return {"recommendations": [], "explanation": "No matching policies found for your profile.", "profile": profile}

    groq_messages = [
        {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"User Profile:\n{json.dumps(profile, indent=2)}\n\nMatching Policies:\n{json.dumps(policies, indent=2)}\n\nProvide recommendations ranked by relevance."}
    ]

    explanation = call_groq(groq_messages)

    return {
        "recommendations": policies,
        "explanation": explanation,
        "profile": profile,
        "count": len(policies)
    }

# ── Policy Comparison ──────────────────────────────────────

@app.post("/api/policies/compare")
async def compare_policies(req: CompareRequest):
    if len(req.policy_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 policies to compare")
    if len(req.policy_ids) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 policies can be compared")

    remaining_ids = set(req.policy_ids)
    found_by_id: dict = {}

    for collection in policy_query_collections():
        if not remaining_ids:
            break
        cursor = collection.find({"policy_id": {"$in": list(remaining_ids)}})
        async for doc in cursor:
            policy = _serialize_policy(doc)
            policy_id = policy.get("policy_id")
            if not policy_id or policy_id in found_by_id:
                continue
            found_by_id[policy_id] = policy
            remaining_ids.discard(policy_id)

    policies = [found_by_id[pid] for pid in req.policy_ids if pid in found_by_id]

    if len(policies) < 2:
        raise HTTPException(status_code=404, detail="Could not find enough policies to compare")

    return {"policies": policies, "count": len(policies)}

# ── Applications (MongoDB-persisted, user-scoped) ──────────

@app.post("/api/applications")
async def create_application(
    req: ApplicationRequest,
    current_user: dict = Depends(get_current_user),
):
    policy = await _find_policy_by_id(req.policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    app_number = generate_app_number()
    now = datetime.now(timezone.utc).isoformat()

    application = {
        "application_number": app_number,
        "application_id": app_number,
        "user_id": current_user["user_id"],
        "user_email": current_user["email"],
        "session_id": req.session_id,
        "policy_id": req.policy_id,
        "policy_name": policy["name"],
        "provider": policy["provider"],
        "category": policy["category"],
        "user_profile": req.user_profile,
        "status": "submitted",
        "status_history": [
            {
                "status": "submitted",
                "timestamp": now,
                "note": "Application submitted successfully",
            }
        ],
        "created_at": now,
        "updated_at": now,
    }

    result = await db.applications.insert_one(application)
    application["_id"] = str(result.inserted_id)
    return {"application": application}


@app.get("/api/applications")
async def get_applications(current_user: dict = Depends(get_current_user)):
    cursor = db.applications.find(
        {"user_id": current_user["user_id"]},
        sort=[("created_at", -1)],
    )
    apps = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        apps.append(doc)
    return {"applications": apps, "count": len(apps)}


@app.patch("/api/applications/{application_number}")
async def update_application(
    application_number: str,
    req: ApplicationUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    valid_statuses = {"submitted", "under_review", "approved", "rejected"}
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    now = datetime.now(timezone.utc).isoformat()
    result = await db.applications.find_one_and_update(
        {"application_number": application_number, "user_id": current_user["user_id"]},
        {
            "$set": {"status": req.status, "updated_at": now},
            "$push": {
                "status_history": {
                    "status": req.status,
                    "timestamp": now,
                    "note": f"Status updated to {req.status}",
                }
            },
        },
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    result["_id"] = str(result["_id"])
    return {"application": result}

# ── Agent Action ───────────────────────────────────────────

@app.post("/api/chat/agent-action")
async def agent_action(req: AgentActionRequest):
    conversation = conversations_store.get(req.session_id, {})

    groq_messages = [{"role": "system", "content": AVATAR_SYSTEM_PROMPT}]
    for msg in conversation.get("messages", []):
        groq_messages.append({"role": msg["role"], "content": msg["content"]})

    if req.action_type == "application_submitted":
        d = req.action_data
        hint = (
            f"[SYSTEM: The user just submitted an application. "
            f"Application Number: {d.get('application_id')}, "
            f"Policy: {d.get('policy_name')}, "
            f"Provider: {d.get('provider')}, "
            f"Status: submitted. "
            f"Generate a warm professional confirmation for the user, "
            f"clearly stating the Application Number and that they can track it in the Application Tracker.]"
        )
    else:
        hint = f"[SYSTEM: {req.action_type} — {json.dumps(req.action_data)}. Acknowledge to the user appropriately.]"

    groq_messages.append({"role": "user", "content": hint})
    ai_response = call_groq(groq_messages)

    if req.session_id not in conversations_store:
        conversations_store[req.session_id] = {
            "session_id": req.session_id,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    conversations_store[req.session_id]["messages"].append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {"response": ai_response, "session_id": req.session_id}

# ── News ───────────────────────────────────────────────────

@app.get("/api/news")
async def get_news(category: Optional[str] = Query(None)):
    global _news_cache

    now_ts = datetime.now(timezone.utc).timestamp()
    cache_stale = (
        _news_cache["fetched_at"] is None
        or (now_ts - _news_cache["fetched_at"]) >= NEWS_CACHE_TTL
    )

    is_live = False
    if cache_stale and NEWS_API_KEY:
        try:
            articles = await fetch_live_news()
            if articles:
                _news_cache = {"articles": articles, "fetched_at": now_ts}
                is_live = True
        except Exception as e:
            print(f"[News] Live fetch failed: {e}")

    if _news_cache["articles"]:
        news = _news_cache["articles"]
        is_live = True
    else:
        news = list(news_store)

    if category:
        news = [n for n in news if n.get("category") == category]

    fetched_at = (
        datetime.fromtimestamp(_news_cache["fetched_at"], tz=timezone.utc).isoformat()
        if _news_cache["fetched_at"]
        else None
    )
    return {"news": news, "count": len(news), "is_live": is_live, "fetched_at": fetched_at}

# ── Open Chat ──────────────────────────────────────────────

OPEN_CHAT_SYSTEM = """You are Fin-ae, a knowledgeable AI financial assistant specializing in the UAE market. Answer financial questions clearly and concisely. Cover topics like:
- Banking and savings strategies
- Investment principles and options in UAE
- Insurance guidance
- Loan and mortgage advice
- Credit card optimization
- Tax-free income benefits in UAE
- Financial planning basics

Always clarify you're providing educational information, not regulated financial advice. Keep answers focused and practical."""

@app.post("/api/chat/open")
async def open_chat(req: OpenChatRequest):
    chat_key = f"open_{req.session_id}"
    if chat_key not in open_chats_store:
        open_chats_store[chat_key] = {
            "session_id": chat_key,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    conversation = open_chats_store[chat_key]

    groq_messages = [{"role": "system", "content": OPEN_CHAT_SYSTEM}]
    for msg in conversation["messages"][-20:]:
        groq_messages.append({"role": msg["role"], "content": msg["content"]})
    groq_messages.append({"role": "user", "content": req.message})

    ai_response = call_groq(groq_messages)

    now = datetime.now(timezone.utc).isoformat()
    conversation["messages"].append({"role": "user", "content": req.message, "timestamp": now})
    conversation["messages"].append({"role": "assistant", "content": ai_response, "timestamp": now})

    return {"response": ai_response, "session_id": req.session_id}

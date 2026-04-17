import os
import json
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ─── In-Memory Store ───────────────────────────────────────

policies_store: list = []
news_store: list = []
conversations_store: dict = {}
profiles_store: dict = {}
applications_store: dict = {}
open_chats_store: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_data()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic Models ──────────────────────────────────────

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
    session_id: str
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
    }
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
        "image_key": "credit_card_mockup",
        "impact": "More choice for Sharia-compliant investing. Review your portfolio allocation."
    },
    {
        "news_id": "news-004",
        "title": "Credit Card Spending in UAE Grows 18% Year-on-Year",
        "summary": "Card spending surged driven by digital payments adoption and reward program enhancements by major banks.",
        "category": "banking",
        "date": "2026-01-08",
        "source": "Khaleej Times",
        "image_key": "credit_card_mockup",
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
        "image_key": "dubai_skyline_news_1",
        "impact": "Excellent time to consolidate debt or finance major purchases."
    }
]

def seed_data():
    global policies_store, news_store
    policies_store = list(FINANCIAL_POLICIES)
    news_store = list(FINANCIAL_NEWS)
    print(f"Loaded {len(policies_store)} policies and {len(news_store)} news articles")

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

## Information Gathering Steps

When a user expresses interest in a financial product, follow these steps **one at a time**:

**Step 1 — Identify the Goal**
Confirm what product category they need: insurance, loan, credit card, investment, or bank account. Acknowledge their choice warmly.

**Step 2 — Personal Details** (one question per message)
- Full name and age
- Nationality and UAE residency status (resident / visitor / citizen)

**Step 3 — Financial Profile** (one question per message)
- Monthly income / salary in AED
- Employment type: salaried, self-employed, or business owner

**Step 4 — Preferences** (one question per message)
- Risk appetite: conservative, moderate, or aggressive
- Sharia-compliant products preference (yes / no)
- Any specific requirements or concerns

**Step 5 — Confirmation**
Once you have gathered enough information, summarise what you have learned and let the user know you are finding the best matching products:

> "Based on what you've shared, I have everything I need. Let me find the best **[product type]** options for you..."

## Formatting Rules
- Use **bold** for product names, key figures, and important terms
- Use `-` bullet lists for options or benefits
- Use numbered lists for sequential steps
- Keep each response to 2–4 sentences or a short list — never a wall of text
- **Never ask more than one question at a time**

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

# ─── API Routes ────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "finae-api"}

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

@app.get("/api/policies")
async def get_policies(
    category: Optional[str] = Query(None),
    sharia_compliant: Optional[bool] = Query(None),
    min_salary: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
):
    policies = list(policies_store)
    if category:
        policies = [p for p in policies if p.get("category") == category]
    if sharia_compliant is not None:
        policies = [p for p in policies if p.get("sharia_compliant") == sharia_compliant]
    if risk_level:
        policies = [p for p in policies if p.get("risk_level") == risk_level]
    if min_salary:
        policies = [p for p in policies if p.get("min_salary", 0) <= min_salary]
    return {"policies": policies, "count": len(policies)}

@app.get("/api/policies/{policy_id}")
async def get_policy(policy_id: str):
    policy = next((p for p in policies_store if p["policy_id"] == policy_id), None)
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
    }

    policies = list(policies_store)
    if req.category:
        policies = [p for p in policies if p.get("category") == req.category]
    elif profile.get("financial_goal"):
        mapped = goal_map.get(profile["financial_goal"].lower())
        if mapped:
            policies = [p for p in policies if p.get("category") == mapped]

    if profile.get("sharia_compliant"):
        policies = [p for p in policies if p.get("sharia_compliant") is True]

    salary = profile.get("monthly_salary")
    if salary:
        policies = [p for p in policies if p.get("min_salary", 0) <= salary]

    age = profile.get("age")
    if age:
        policies = [p for p in policies if p.get("min_age", 0) <= age <= p.get("max_age", 100)]

    if not policies:
        return {"recommendations": [], "explanation": "No matching policies found for your profile.", "profile": profile}

    groq_messages = [
        {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"User Profile:\n{json.dumps(profile, indent=2)}\n\nMatching Policies:\n{json.dumps(policies, indent=2)}\n\nProvide recommendations ranked by relevance."}
    ]

    explanation = call_groq(groq_messages)
    policies.sort(key=lambda x: x.get("rating", 0), reverse=True)

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

    policies = [p for p in policies_store if p["policy_id"] in req.policy_ids]

    if len(policies) < 2:
        raise HTTPException(status_code=404, detail="Could not find enough policies to compare")

    return {"policies": policies, "count": len(policies)}

# ── Applications ───────────────────────────────────────────

@app.post("/api/applications")
async def create_application(req: ApplicationRequest):
    policy = next((p for p in policies_store if p["policy_id"] == req.policy_id), None)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    application = {
        "application_id": f"APP-{uuid.uuid4().hex[:8].upper()}",
        "session_id": req.session_id,
        "policy_id": req.policy_id,
        "policy_name": policy["name"],
        "provider": policy["provider"],
        "category": policy["category"],
        "user_profile": req.user_profile,
        "status": "submitted",
        "status_history": [
            {"status": "submitted", "timestamp": datetime.now(timezone.utc).isoformat(), "note": "Application submitted successfully"}
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    applications_store[application["application_id"]] = application
    return {"application": application}

@app.get("/api/applications/{session_id}")
async def get_applications(session_id: str):
    apps = [a for a in applications_store.values() if a["session_id"] == session_id]
    return {"applications": apps, "count": len(apps)}

@app.patch("/api/applications/{application_id}")
async def update_application(application_id: str, req: ApplicationUpdateRequest):
    app_doc = applications_store.get(application_id)
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")

    app_doc["status"] = req.status
    app_doc["status_history"].append({
        "status": req.status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": f"Status updated to {req.status}"
    })
    return {"application": app_doc}

# ── Agent Action (system-triggered agent message) ─────────

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
            f"Application ID: {d.get('application_id')}, "
            f"Policy: {d.get('policy_name')}, "
            f"Provider: {d.get('provider')}, "
            f"Status: submitted. "
            f"Generate a warm professional confirmation for the user, "
            f"clearly stating the Application ID and that they can track it in the Application Tracker.]"
        )
    else:
        hint = f"[SYSTEM: {req.action_type} — {json.dumps(req.action_data)}. Acknowledge to the user appropriately.]"

    groq_messages.append({"role": "user", "content": hint})
    ai_response = call_groq(groq_messages)

    if req.session_id not in conversations_store:
        conversations_store[req.session_id] = {"session_id": req.session_id, "messages": [], "created_at": datetime.now(timezone.utc).isoformat()}
    conversations_store[req.session_id]["messages"].append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {"response": ai_response, "session_id": req.session_id}

# ── News ───────────────────────────────────────────────────

@app.get("/api/news")
async def get_news(category: Optional[str] = Query(None)):
    news = list(news_store)
    if category:
        news = [n for n in news if n.get("category") == category]
    return {"news": news, "count": len(news)}

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

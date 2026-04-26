import json

from fastapi import APIRouter, HTTPException

from core.db import normalize_policy_category
from core.llm import call_groq
from core.models import RecommendRequest
from core.stores import profiles_store
from routers.chat import RECOMMENDATION_SYSTEM_PROMPT
from routers.policies import _find_policies

router = APIRouter()


@router.post("/api/policies/recommend")
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

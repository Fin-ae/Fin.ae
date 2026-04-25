"""
ai_chat.py
All Groq LLM calls for Fin.ae are centralised here.

Uses the Groq Python SDK. The API key is loaded from the
environment variable GROQ_API_KEY — never hard-coded.
Follows the secrets pattern from Guide Book 1, Chapter 2.
"""

import os
import json
import logging
from groq import Groq

log = logging.getLogger(__name__)

# ── Groq client — created once at module level ───────────────────
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"

# ── System prompts ────────────────────────────────────────────────
ADVISOR_SYSTEM_PROMPT = """
You are Fin, a friendly and knowledgeable UAE financial adviser on the Fin.ae platform.
You help users discover the best financial products — credit cards, loans, bank accounts,
insurance, and investments — from UAE banks and providers.

Your job in this conversation is to gently profile the user by asking about:
- Their monthly salary (in AED)
- Their age
- Whether they are a UAE resident, citizen, or non-resident
- Whether they require Sharia-compliant products
- Their risk appetite (low, medium, high)
- Their financial goals (e.g. cashback, travel, saving, home purchase)

Ask one question at a time. Be warm and conversational — never clinical.
Once you have enough information (at least salary and residency), tell the user you have
great product matches for them and that you will show their personalised recommendations.
"""

OPEN_CHAT_SYSTEM_PROMPT = """
You are Fin, a knowledgeable UAE financial adviser on Fin.ae.
Answer any financial question the user has — covering UAE banking, investments,
insurance, credit, Sharia finance, and general personal finance.
Be clear, concise, and helpful. Always note that your answers are for informational
purposes only and users should consult a qualified adviser for major decisions.
"""


def chat_with_groq(messages: list[dict], system_prompt: str = ADVISOR_SYSTEM_PROMPT) -> dict:
    """
    Send a conversation to Groq and return the assistant reply.

    Args:
        messages: List of {"role": "user"/"assistant", "content": "..."} dicts
        system_prompt: The system instruction to prepend

    Returns:
        dict with keys: reply, profile_complete, suggested_action
    """
    groq_messages = [{"role": "system", "content": system_prompt}] + messages

    response = client.chat.completions.create(
        model=MODEL,
        messages=groq_messages,
        max_tokens=512,
        temperature=0.7,
    )

    reply = response.choices[0].message.content.strip()

    # Simple heuristic: if reply mentions showing recommendations, profile is complete
    profile_complete = any(
        phrase in reply.lower()
        for phrase in ["personalised recommendations", "great matches", "show you", "found some"]
    )

    return {
        "reply": reply,
        "profile_complete": profile_complete,
        "suggested_action": "show_recommendations" if profile_complete else "ask_more",
    }


def open_chat(messages: list[dict]) -> dict:
    """General Q&A chat with no profiling logic."""
    return chat_with_groq(messages, system_prompt=OPEN_CHAT_SYSTEM_PROMPT)


def extract_profile(messages: list[dict]) -> dict:
    """
    Analyse a completed conversation and extract a structured UserProfile.
    Prompts the model to respond in JSON only — following the structured
    output pattern from Guide Book 1 capstone.
    """
    conversation_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )

    extraction_prompt = f"""
Analyse this conversation between a financial adviser and a user.
Extract the user's financial profile and respond ONLY with a valid JSON object.
Do not include any explanation, preamble, or markdown code fences.

Conversation:
{conversation_text}

Respond with this exact JSON structure (use null for any unknown fields):
{{
  "age": null,
  "monthly_salary": null,
  "residency": null,
  "risk_appetite": null,
  "sharia_required": null,
  "goals": []
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": extraction_prompt}],
        max_tokens=256,
        temperature=0.1,  # low temperature for structured output
    )

    raw = response.choices[0].message.content.strip()

    # Strip any accidental markdown fences — Guide Book 1 error handling pattern
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        profile = json.loads(raw)
        confidence = _score_profile_confidence(profile)
    except json.JSONDecodeError:
        log.error(f"Failed to parse profile JSON: {raw}")
        profile = {}
        confidence = 0.0

    return {"profile": profile, "confidence": confidence}


def _score_profile_confidence(profile: dict) -> float:
    """Score how complete the extracted profile is (0.0 to 1.0)."""
    key_fields = ["age", "monthly_salary", "residency", "risk_appetite", "sharia_required"]
    filled = sum(1 for f in key_fields if profile.get(f) is not None)
    return round(filled / len(key_fields), 2)


def get_ai_recommendations(profile: dict, products: list[dict], category: str | None) -> list[dict]:
    """
    Ask the AI to rank and explain product recommendations for a given profile.

    Returns a list of {"product": {...}, "score": 0.0-1.0, "rationale": "..."} dicts.
    """
    # Filter by category first if specified
    if category:
        filtered = [p for p in products if p["category"] == category]
    else:
        filtered = products

    if not filtered:
        return []

    product_summary = json.dumps(
        [{"id": p["id"], "name": p["name"], "category": p["category"],
          "sharia": p["sharia"], "min_salary": p["min_salary"],
          "key_features": p["key_features"][:2]} for p in filtered],
        indent=2
    )

    prompt = f"""
You are a UAE financial adviser. Given this user profile and list of products,
rank the top 3 most suitable products and explain why.

User Profile:
{json.dumps(profile, indent=2)}

Available Products:
{product_summary}

Respond ONLY with a valid JSON array. No explanation, no markdown fences.
Format:
[
  {{"product_id": "prod_001", "score": 0.95, "rationale": "Explanation here"}},
  {{"product_id": "prod_002", "score": 0.80, "rationale": "Explanation here"}},
  {{"product_id": "prod_003", "score": 0.65, "rationale": "Explanation here"}}
]
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        ranked = json.loads(raw)
    except json.JSONDecodeError:
        log.error(f"Failed to parse recommendations JSON: {raw}")
        return []

    # Join back with full product objects
    product_map = {p["id"]: p for p in filtered}
    results = []
    for item in ranked:
        pid = item.get("product_id")
        if pid and pid in product_map:
            results.append({
                "product": product_map[pid],
                "score": item.get("score", 0.5),
                "rationale": item.get("rationale", ""),
            })

    return results

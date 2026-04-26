import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from core.llm import call_groq
from core.models import (
    AgentActionRequest,
    ChatMessageRequest,
    ExtractProfileRequest,
    OpenChatRequest,
)
from core.stores import (
    conversations_store,
    open_chats_store,
    profiles_store,
)

router = APIRouter()


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

OPEN_CHAT_SYSTEM = """You are Fin-ae, a knowledgeable AI financial assistant specializing in the UAE market. Answer financial questions clearly and concisely. Cover topics like:
- Banking and savings strategies
- Investment principles and options in UAE
- Insurance guidance
- Loan and mortgage advice
- Credit card optimization
- Tax-free income benefits in UAE
- Financial planning basics

Always clarify you're providing educational information, not regulated financial advice. Keep answers focused and practical."""


@router.post("/api/chat/message")
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


@router.post("/api/chat/extract-profile")
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


@router.post("/api/chat/agent-action")
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


@router.post("/api/chat/open")
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

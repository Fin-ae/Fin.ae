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


AVATAR_SYSTEM_PROMPT = ""            
EXTRACTION_SYSTEM_PROMPT = ""       
RECOMMENDATION_SYSTEM_PROMPT = ""   
OPEN_CHAT_SYSTEM = ""               


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
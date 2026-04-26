from typing import Optional

from pydantic import BaseModel


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

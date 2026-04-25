"""
models.py
All Pydantic request and response models for the Fin.ae API.
These are used by FastAPI to automatically validate incoming data
and generate the /docs OpenAPI documentation.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ─────────────────────────────────────────
# CHAT MODELS
# ─────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single message in a conversation."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    """Request body for /api/chat/message and /api/chat/open."""
    session_id: str = Field(..., description="UUID identifying this user session")
    messages: list[ChatMessage] = Field(..., description="Full conversation history")


class AgentActionRequest(BaseModel):
    """Request body for /api/chat/agent-action."""
    session_id: str
    action: str = Field(..., description="apply | compare | callback | save_product")
    product_id: Optional[str] = None
    metadata: Optional[dict] = None


# ─────────────────────────────────────────
# USER PROFILE MODEL
# ─────────────────────────────────────────

class UserProfile(BaseModel):
    """Structured user financial profile extracted from chat."""
    age: Optional[int] = None
    monthly_salary: Optional[int] = None
    residency: Optional[str] = Field(None, description="resident | non_resident | citizen")
    risk_appetite: Optional[str] = Field(None, description="low | medium | high")
    sharia_required: Optional[bool] = None
    goals: Optional[list[str]] = None


class RecommendRequest(BaseModel):
    """Request body for /api/policies/recommend."""
    session_id: str
    category: Optional[str] = None
    profile: UserProfile


# ─────────────────────────────────────────
# PRODUCT MODELS
# ─────────────────────────────────────────

class CompareRequest(BaseModel):
    """Request body for /api/policies/compare."""
    product_ids: list[str] = Field(..., min_length=2, max_length=4,
                                   description="List of 2 to 4 product IDs to compare")


# ─────────────────────────────────────────
# APPLICATION / LEAD MODELS
# ─────────────────────────────────────────

class ApplicationCreate(BaseModel):
    """Request body for POST /api/applications."""
    session_id: str
    product_id: str
    product_name: str
    applicant_name: str
    phone: str
    email: Optional[str] = None
    preferred_time: Optional[str] = Field(None, description="morning | afternoon | evening")
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    """Request body for PATCH /api/applications/{id}."""
    status: str = Field(..., description="pending | in_review | approved | rejected")
    notes: Optional[str] = None

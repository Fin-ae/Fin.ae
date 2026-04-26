from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from core import db as db_module
from core.auth import (
    create_token,
    get_current_user,
    hash_password,
    verify_password,
)
from core.models import LoginRequest, RegisterRequest

router = APIRouter()


@router.post("/api/auth/register")
async def register(req: RegisterRequest):
    if not req.email or not req.password or not req.name:
        raise HTTPException(status_code=400, detail="Email, password and name are required")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = await db_module.db.users.find_one({"email": req.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "email": req.email.lower(),
        "name": req.name.strip(),
        "password_hash": hash_password(req.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db_module.db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    token = create_token(user_id, req.email.lower())
    return {
        "token": token,
        "user": {"id": user_id, "email": req.email.lower(), "name": req.name.strip()},
    }


@router.post("/api/auth/login")
async def login(req: LoginRequest):
    user = await db_module.db.users.find_one({"email": req.email.lower()})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_token(user_id, req.email.lower())
    return {
        "token": token,
        "user": {"id": user_id, "email": user["email"], "name": user["name"]},
    }


@router.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db_module.db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": {"id": str(user["_id"]), "email": user["email"], "name": user["name"]}}

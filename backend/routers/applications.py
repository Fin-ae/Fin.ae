from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from core import db as db_module
from core.auth import generate_app_number, get_current_user
from core.models import ApplicationRequest, ApplicationUpdateRequest
from routers.policies import _find_policy_by_id

router = APIRouter()


@router.post("/api/applications")
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

    result = await db_module.db.applications.insert_one(application)
    application["_id"] = str(result.inserted_id)
    return {"application": application}


@router.get("/api/applications")
async def get_applications(current_user: dict = Depends(get_current_user)):
    cursor = db_module.db.applications.find(
        {"user_id": current_user["user_id"]},
        sort=[("created_at", -1)],
    )
    apps = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        apps.append(doc)
    return {"applications": apps, "count": len(apps)}


@router.patch("/api/applications/{application_number}")
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
    result = await db_module.db.applications.find_one_and_update(
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

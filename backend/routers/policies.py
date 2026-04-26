from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from core.db import (
    infer_category_from_policy_id,
    normalize_policy_category,
    policy_query_collections,
)
from core.models import CompareRequest

router = APIRouter()


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


@router.get("/api/policies")
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


@router.get("/api/policies/{policy_id}")
async def get_policy(policy_id: str):
    policy = await _find_policy_by_id(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policy": policy}


@router.post("/api/policies/compare")
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

from fastapi import APIRouter, Depends, HTTPException

from backend.database import database
from backend.services.security import current_user
from backend.services.serializers import serialize

router = APIRouter(prefix="/api/platform", tags=["super admin"])


def super_admin(user=Depends(current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Platform administrator access required")
    return user


@router.get("/businesses")
def list_platform_businesses(user=Depends(super_admin)):
    results = []
    for business in database.businesses.find().sort("name", 1):
        item = serialize(business)
        item["users"] = database.users.count_documents({"business_id": item["id"]})
        item["orders"] = database.orders.count_documents({"business_id": item["id"]})
        results.append(item)
    return results

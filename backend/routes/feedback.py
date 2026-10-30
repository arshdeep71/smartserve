from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi import Depends

from backend.database import database
from backend.models.documents import FeedbackCreate
from backend.services.serializers import serialize
from backend.services.security import business_access, require_roles

router = APIRouter(prefix="/api/businesses/{business_id}/feedback", tags=["feedback"])


def require_business(business_id):
    if not ObjectId.is_valid(business_id) or not database.businesses.find_one({"_id": ObjectId(business_id)}):
        raise HTTPException(status_code=404, detail="Business not found")


@router.post("", status_code=201)
def submit_feedback(business_id: str, payload: FeedbackCreate):
    require_business(business_id)
    document = payload.model_dump()
    document["business_id"] = business_id
    result = database.feedback.insert_one(document)
    document["_id"] = result.inserted_id
    return {"id": str(result.inserted_id), "message": "Thank you for your feedback"}


@router.get("")
def list_feedback(business_id: str, user=Depends(require_roles("admin", "manager"))):
    require_business(business_id)
    return [serialize(row) for row in database.feedback.find({"business_id": business_id}).sort("submitted_at", -1)]


@router.get("/summary")
def feedback_summary(business_id: str, user=Depends(require_roles("admin", "manager"))):
    require_business(business_id)
    rows = list(database.feedback.find({"business_id": business_id}))
    total = len(rows)
    likes = sum(row["opinion"] == "liked" for row in rows)
    dislikes = sum(row["opinion"] == "disliked" for row in rows)
    complaints = {}
    requests = {}
    for row in rows:
        if row.get("complaint"):
            complaints[row["complaint"]] = complaints.get(row["complaint"], 0) + 1
        if row.get("requested_dish"):
            dish = row["requested_dish"].strip()
            requests[dish] = requests.get(dish, 0) + 1
    return {
        "total": total,
        "liked_percent": round(likes * 100 / total, 1) if total else 0,
        "disliked_percent": round(dislikes * 100 / total, 1) if total else 0,
        "top_complaints": sorted(complaints.items(), key=lambda item: item[1], reverse=True),
        "requested_dishes": sorted(requests.items(), key=lambda item: item[1], reverse=True),
    }

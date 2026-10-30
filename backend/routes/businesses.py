from fastapi import APIRouter, HTTPException, Request

from backend.database import database
from backend.models.documents import BusinessCreate, utc_now
from backend.services.serializers import serialize

router = APIRouter(prefix="/api/businesses", tags=["businesses"])


@router.post("", status_code=201)
def create_business(payload: BusinessCreate, request: Request):
    if request.client.host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
        raise HTTPException(status_code=403, detail="Initial setup is available only from this computer")
    document = payload.model_dump()
    document["created_at"] = utc_now()
    result = database.businesses.insert_one(document)
    document["_id"] = result.inserted_id
    return serialize(document)


@router.get("")
def list_businesses():
    return [serialize(item) for item in database.businesses.find().sort("name", 1)]


@router.get("/pending-setup")
def list_pending_setup(request: Request):
    if request.client.host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
        raise HTTPException(status_code=403, detail="Initial setup is available only from this computer")
    pending = []
    for business in database.businesses.find().sort("created_at", -1):
        business_id = str(business["_id"])
        if database.users.count_documents({"business_id": business_id}) == 0:
            pending.append({"id": business_id, "name": business["name"], "business_type": business["business_type"]})
    return pending


@router.get("/{business_id}")
def get_business(business_id: str):
    from bson import ObjectId
    if not ObjectId.is_valid(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    business = database.businesses.find_one({"_id": ObjectId(business_id)})
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return serialize(business)

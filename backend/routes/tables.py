from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.database import database
from backend.models.documents import utc_now
from backend.services.security import require_roles

router = APIRouter(prefix="/api/businesses/{business_id}/tables", tags=["restaurant tables"])


class TableCreate(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    seats: int = Field(default=2, ge=1, le=50)


def require_business(business_id):
    if not ObjectId.is_valid(business_id) or not database.businesses.find_one({"_id": ObjectId(business_id), "business_type": "restaurant"}):
        raise HTTPException(status_code=404, detail="Restaurant not found")


@router.get("")
def list_tables(business_id: str, user=Depends(require_roles("admin", "manager", "cashier"))):
    require_business(business_id)
    return [{**{key: value for key, value in row.items() if key != "_id"}, "id": str(row["_id"])} for row in database.tables.find({"business_id": business_id}).sort("name", 1)]


@router.post("", status_code=201)
def add_table(business_id: str, payload: TableCreate, user=Depends(require_roles("admin", "manager"))):
    require_business(business_id)
    row = {**payload.model_dump(), "business_id": business_id, "status": "available", "created_at": utc_now()}
    result = database.tables.insert_one(row)
    return {"id": str(result.inserted_id), **payload.model_dump(), "status": "available"}


@router.patch("/{table_id}/status")
def set_table_status(business_id: str, table_id: str, status: str, user=Depends(require_roles("admin", "manager", "cashier"))):
    require_business(business_id)
    if status not in {"available", "occupied", "reserved"}:
        raise HTTPException(status_code=422, detail="Status must be available, occupied, or reserved")
    if not ObjectId.is_valid(table_id):
        raise HTTPException(status_code=404, detail="Table not found")
    result = database.tables.update_one({"_id": ObjectId(table_id), "business_id": business_id}, {"$set": {"status": status}})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Table not found")
    return {"id": table_id, "status": status}

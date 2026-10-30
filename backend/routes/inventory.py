from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.database import database
from backend.models.documents import utc_now
from backend.services.security import business_access, require_roles

router = APIRouter(prefix="/api/businesses/{business_id}/inventory", tags=["inventory"])


class StockUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: float = Field(ge=0)
    unit: str = Field(default="units", max_length=20)
    low_stock_at: float = Field(default=5, ge=0)


def require_business(business_id):
    if not ObjectId.is_valid(business_id) or not database.businesses.find_one({"_id": ObjectId(business_id)}):
        raise HTTPException(status_code=404, detail="Business not found")


@router.get("")
def list_inventory(business_id: str, user=Depends(business_access)):
    require_business(business_id)
    return [{**{key: value for key, value in row.items() if key != "_id"}, "id": str(row["_id"])} for row in database.inventory.find({"business_id": business_id}).sort("name", 1)]


@router.put("")
def update_stock(business_id: str, payload: StockUpdate, user=Depends(require_roles("admin", "manager"))):
    require_business(business_id)
    existing = database.inventory.find_one({"business_id": business_id, "name": payload.name})
    previous_quantity = existing.get("quantity", 0) if existing else 0
    database.inventory.update_one(
        {"business_id": business_id, "name": payload.name},
        {"$set": {**payload.model_dump(), "updated_at": utc_now()}, "$setOnInsert": {"business_id": business_id}},
        upsert=True,
    )
    quantity_change = payload.quantity - previous_quantity
    if quantity_change:
        database.stock_movements.insert_one({
            "business_id": business_id,
            "item_name": payload.name,
            "quantity_change": quantity_change,
            "note": "Initial stock entry" if existing is None else "Manual stock adjustment",
            "recorded_at": utc_now(),
            "recorded_by": user.get("sub"),
        })
    return {"message": "Stock updated", "item": payload.model_dump()}

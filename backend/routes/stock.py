from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.database import database
from backend.models.documents import utc_now
from backend.services.security import require_roles

router = APIRouter(prefix="/api/businesses/{business_id}/stock-movements", tags=["inventory"])


class Movement(BaseModel):
    item_name: str = Field(min_length=1, max_length=100)
    quantity_change: float
    note: str = Field(default="", max_length=250)


@router.post("", status_code=201)
def record_movement(business_id: str, payload: Movement, user=Depends(require_roles("admin", "manager"))):
    if not ObjectId.is_valid(business_id) or not database.businesses.find_one({"_id": ObjectId(business_id)}):
        raise HTTPException(status_code=404, detail="Business not found")
    stock = database.inventory.find_one({"business_id": business_id, "name": payload.item_name})
    if not stock:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    next_quantity = stock["quantity"] + payload.quantity_change
    if next_quantity < 0:
        raise HTTPException(status_code=422, detail="Stock cannot become negative")
    database.inventory.update_one({"_id": stock["_id"]}, {"$set": {"quantity": next_quantity, "updated_at": utc_now()}})
    movement = {**payload.model_dump(), "business_id": business_id, "recorded_at": utc_now(), "recorded_by": user["sub"]}
    database.stock_movements.insert_one(movement)
    return {"item_name": payload.item_name, "quantity": next_quantity}


@router.get("")
def list_movements(business_id: str, user=Depends(require_roles("admin", "manager"))):
    if not ObjectId.is_valid(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    return [{**{key: value for key, value in row.items() if key != "_id"}, "id": str(row["_id"])} for row in database.stock_movements.find({"business_id": business_id}).sort("recorded_at", -1).limit(100)]

from uuid import uuid4

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from backend.database import database
from backend.models.documents import OrderCreate, utc_now
from backend.services.serializers import serialize
from backend.services.security import business_access
from fastapi import Depends

router = APIRouter(prefix="/api/businesses/{business_id}/orders", tags=["orders"])


@router.post("", status_code=201)
def create_order(business_id: str, payload: OrderCreate, user=Depends(business_access)):
    if not ObjectId.is_valid(business_id) or not database.businesses.find_one({"_id": ObjectId(business_id)}):
        raise HTTPException(status_code=404, detail="Business not found")
    items = []
    stock_deductions = {}
    for line in payload.items:
        menu_item = database.menu_items.find_one({"_id": ObjectId(line.item_id), "business_id": business_id, "available": True}) if ObjectId.is_valid(line.item_id) else None
        if not menu_item:
            raise HTTPException(status_code=422, detail=f"Menu item is unavailable: {line.name}")
        size_price = menu_item.get("sizes", {}).get(line.size, 0) if line.size else 0
        if line.size and line.size not in menu_item.get("sizes", {}):
            raise HTTPException(status_code=422, detail=f"Invalid size for {line.name}")
        addon_cost = 0
        for addon in line.add_ons:
            if addon not in menu_item.get("add_ons", {}):
                raise HTTPException(status_code=422, detail=f"Invalid add-on for {line.name}: {addon}")
            addon_cost += menu_item["add_ons"][addon]
        price = menu_item["price"] + size_price + addon_cost
        items.append({**line.model_dump(), "name": menu_item["name"], "unit_price": price})
        for ingredient, amount in menu_item.get("recipe", {}).items():
            stock_deductions[ingredient] = stock_deductions.get(ingredient, 0) + amount * line.quantity
    total = round(sum(line["quantity"] * line["unit_price"] for line in items), 2)
    adjusted = []
    for ingredient, amount in stock_deductions.items():
        result = database.inventory.update_one({"business_id": business_id, "name": ingredient, "quantity": {"$gte": amount}}, {"$inc": {"quantity": -amount}})
        if not result.modified_count:
            for name, deduction in adjusted:
                database.inventory.update_one({"business_id": business_id, "name": name}, {"$inc": {"quantity": deduction}})
            raise HTTPException(status_code=409, detail=f"Not enough stock for {ingredient}")
        adjusted.append((ingredient, amount))
    document = payload.model_dump(exclude={"items"})
    document.update(
        order_id=f"SS-{uuid4().hex[:10].upper()}", business_id=business_id,
        items=items, total=total,
        status="completed" if payload.order_type == "counter" else "pending",
        created_at=utc_now()
    )
    result = None
    try:
        result = database.orders.insert_one(document)
        if adjusted:
            recorded_at = utc_now()
            database.stock_movements.insert_many([
                {
                    "business_id": business_id,
                    "order_id": document["order_id"],
                    "item_name": ingredient,
                    "quantity_change": -amount,
                    "note": f"Used for order {document['order_id']}",
                    "recorded_at": recorded_at,
                    "recorded_by": user.get("sub"),
                }
                for ingredient, amount in adjusted
            ])
    except Exception:
        if result is not None:
            database.orders.delete_one({"_id": result.inserted_id})
            database.stock_movements.delete_many({"business_id": business_id, "order_id": document["order_id"]})
        for ingredient, amount in adjusted:
            database.inventory.update_one({"business_id": business_id, "name": ingredient}, {"$inc": {"quantity": amount}})
        raise
    document["_id"] = result.inserted_id
    return serialize(document)


@router.get("")
def list_orders(business_id: str, user=Depends(business_access)):
    if not ObjectId.is_valid(business_id) or not database.businesses.find_one({"_id": ObjectId(business_id)}):
        raise HTTPException(status_code=404, detail="Business not found")
    return [serialize(row) for row in database.orders.find({"business_id": business_id}).sort("created_at", -1)]


@router.patch("/{order_id}/status")
def update_order_status(business_id: str, order_id: str, status: str, user=Depends(business_access)):
    if status not in {"pending", "preparing", "ready", "completed", "cancelled"}:
        raise HTTPException(status_code=422, detail="Unsupported order status")
    result = database.orders.update_one({"business_id": business_id, "order_id": order_id}, {"$set": {"status": status}})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order_id, "status": status}

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from math import isfinite
from pydantic import BaseModel, Field, field_validator

from backend.database import database
from backend.models.documents import MenuItemCreate, utc_now
from backend.services.serializers import serialize
from backend.services.security import business_access, require_roles

router = APIRouter(prefix="/api/businesses/{business_id}/menu", tags=["menu"])


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price: float | None = Field(default=None, gt=0)
    available: bool | None = None
    category: str | None = Field(default=None, max_length=50)
    sizes: dict[str, float] | None = None
    add_ons: dict[str, float] | None = None
    recipe: dict[str, float] | None = None

    @field_validator("sizes", "add_ons")
    @classmethod
    def validate_prices(cls, values):
        if values is not None and any(not name.strip() or not isfinite(value) or value < 0 for name, value in values.items()):
            raise ValueError("Option names must be present and option prices must be non-negative numbers")
        return values

    @field_validator("recipe")
    @classmethod
    def validate_recipe(cls, values):
        if values is not None and any(not name.strip() or not isfinite(value) or value <= 0 for name, value in values.items()):
            raise ValueError("Recipe ingredients need names and positive quantities")
        return values


def require_business(business_id):
    if not ObjectId.is_valid(business_id) or not database.businesses.find_one({"_id": ObjectId(business_id)}):
        raise HTTPException(status_code=404, detail="Business not found")


@router.get("")
def list_menu(business_id: str, user=Depends(business_access)):
    require_business(business_id)
    items = database.menu_items.find({"business_id": business_id}).sort("name", 1)
    return [serialize(item) for item in items]


@router.post("", status_code=201)
def add_menu_item(business_id: str, payload: MenuItemCreate, user=Depends(require_roles("admin", "manager"))):
    require_business(business_id)
    document = payload.model_dump()
    document.update(business_id=business_id, created_at=utc_now())
    result = database.menu_items.insert_one(document)
    document["_id"] = result.inserted_id
    return serialize(document)


@router.patch("/{item_id}")
def update_menu_item(business_id: str, item_id: str, payload: MenuItemUpdate, user=Depends(require_roles("admin", "manager"))):
    require_business(business_id)
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=404, detail="Menu item not found")
    changes = {key: value for key, value in payload.model_dump(exclude_unset=True).items() if value is not None}
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one menu field to update")
    result = database.menu_items.update_one(
        {"_id": ObjectId(item_id), "business_id": business_id},
        {"$set": {**changes, "updated_at": utc_now()}},
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return serialize(database.menu_items.find_one({"_id": ObjectId(item_id), "business_id": business_id}))

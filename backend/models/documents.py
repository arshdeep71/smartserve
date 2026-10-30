from datetime import datetime, timezone
from typing import Literal

from math import isfinite
from pydantic import BaseModel, Field, field_validator


def utc_now():
    return datetime.now(timezone.utc)


class BusinessCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    business_type: Literal["canteen", "restaurant", "cafe"]


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    available: bool = True
    category: str = "food"
    sizes: dict[str, float] = Field(default_factory=dict, description="Size name to additional price")
    add_ons: dict[str, float] = Field(default_factory=dict, description="Add-on name to price")
    recipe: dict[str, float] = Field(default_factory=dict, description="Ingredient name to quantity used per sale")

    @field_validator("sizes", "add_ons")
    @classmethod
    def validate_prices(cls, values):
        if any(not name.strip() or not isfinite(value) or value < 0 for name, value in values.items()):
            raise ValueError("Option names must be present and option prices must be non-negative numbers")
        return values

    @field_validator("recipe")
    @classmethod
    def validate_recipe(cls, values):
        if any(not name.strip() or not isfinite(value) or value <= 0 for name, value in values.items()):
            raise ValueError("Recipe ingredients need names and positive quantities")
        return values


class OrderLine(BaseModel):
    item_id: str
    name: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    size: str | None = Field(default=None, max_length=30)
    add_ons: list[str] = Field(default_factory=list)


class OrderCreate(BaseModel):
    items: list[OrderLine] = Field(min_length=1)
    order_type: Literal["dine_in", "takeaway", "counter"] = "counter"
    payment_method: str = "cash"
    receipt_type: Literal["print", "coupon"] = "print"
    coupon_reference: str | None = Field(default=None, max_length=60)
    table_number: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class FeedbackCreate(BaseModel):
    meal: str = Field(min_length=1, max_length=100)
    opinion: Literal["liked", "disliked", "request"]
    complaint: str | None = None
    comment: str | None = Field(default=None, max_length=1000)
    requested_dish: str | None = Field(default=None, max_length=100)
    submitted_at: datetime = Field(default_factory=utc_now)

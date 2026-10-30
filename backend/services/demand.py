"""MongoDB-backed daily item demand forecast lifecycle."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from backend.database import database
from ml.demand_forecasting import aggregate_orders, evaluate_models, predict_next

IST = ZoneInfo("Asia/Kolkata")
FORECASTS = database.demand_forecasts


def ensure_indexes():
    FORECASTS.create_index(
        [("business_id", ASCENDING), ("item_id", ASCENDING), ("forecast_date", ASCENDING)],
        unique=True,
        name="uniq_business_item_forecast_date",
    )


def load_daily_sales(business_id: str):
    orders = list(database.orders.find({"business_id": business_id, "status": "completed"}))
    # Treat each order_id as one transaction, avoiding duplicate stored order documents.
    unique = {}
    for order in orders:
        unique.setdefault(order.get("order_id", str(order.get("_id"))), order)
    items = list(database.menu_items.find({"business_id": business_id}, {"name": 1, "category": 1}))
    names = {str(row["_id"]): row.get("name", "Unknown item") for row in items}
    rows = []
    for order in unique.values():
        stamp = order.get("created_at")
        if isinstance(stamp, datetime):
            day = (stamp.replace(tzinfo=ZoneInfo("UTC")) if stamp.tzinfo is None else stamp).astimezone(IST).date()
            order["created_at"] = day
        elif isinstance(stamp, str):
            try:
                parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                order["created_at"] = parsed.astimezone(IST).date() if parsed.tzinfo else parsed.date()
            except ValueError:
                continue
        rows.append(order)
    daily = aggregate_orders(rows)
    if not daily.empty:
        daily["item"] = daily.apply(lambda row: names.get(row.item_id, row.item), axis=1)
    return daily


def existing_forecast(business_id: str, target: date):
    return list(FORECASTS.find({"business_id": business_id, "forecast_date": target.isoformat()}).sort("item", 1))


def generate_forecast(business_id: str, target_date: date | None = None):
    ensure_indexes()
    daily = load_daily_sales(business_id)
    if daily.empty:
        return {"status": "insufficient_data", "message": "No completed item sales are available yet.", "items": []}
    latest_day = max(daily.date)
    target = target_date or latest_day + timedelta(days=1)
    if target != latest_day + timedelta(days=1):
        return {"status": "insufficient_data", "forecast_date": target.isoformat(), "message": f"Latest completed sales are for {latest_day.isoformat()}; refresh or wait for that date's sales before forecasting.", "items": []}
    cached = existing_forecast(business_id, target)
    if cached:
        return {"status": "ready", "forecast_date": target.isoformat(), "generated_at": cached[0].get("generated_at").isoformat() if cached[0].get("generated_at") else None, "items": [{key: value for key, value in row.items() if key != "_id"} for row in cached], "duplicate_prevented": True}

    evaluation = evaluate_models(daily)
    predictions = predict_next(daily, evaluation)
    # predict_next forecasts the day following actual observations; don't relabel history.
    if not predictions or predictions[0]["forecast_date"] != target.isoformat():
        target = date.fromisoformat(predictions[0]["forecast_date"]) if predictions else target
    generated_at = datetime.now(IST)
    inserted = []
    for prediction in predictions:
        item = {**prediction, "business_id": business_id, "forecast_date": target.isoformat(), "generated_at": generated_at, "evaluation": evaluation}
        try:
            FORECASTS.insert_one(item)
            inserted.append(item)
        except DuplicateKeyError:
            continue
    return {"status": "ready" if inserted else "already_generated", "forecast_date": target.isoformat(), "generated_at": generated_at.isoformat(), "evaluation": evaluation, "items": [{key: value for key, value in row.items() if key not in {"_id", "business_id"}} for row in inserted]}


def forecast_history(business_id: str, limit=60):
    forecasts = list(FORECASTS.find({"business_id": business_id}).sort("forecast_date", -1).limit(limit))
    result = []
    for row in forecasts:
        actual = database.orders.aggregate([
            {"$match": {"business_id": business_id, "status": "completed", "created_at": {"$exists": True}}},
            {"$unwind": "$items"},
            {"$match": {"items.item_id": row.get("item_id")}},
            {"$project": {"day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at", "timezone": "Asia/Kolkata"}}, "quantity": "$items.quantity"}},
            {"$match": {"day": row["forecast_date"]}},
            {"$group": {"_id": None, "quantity": {"$sum": "$quantity"}}},
        ])
        found = next(iter(actual), None)
        result.append({"item": row.get("item"), "item_id": row.get("item_id"), "forecast_date": row.get("forecast_date"), "predicted_quantity": row.get("predicted_quantity"), "actual_quantity": found["quantity"] if found else None, "model_name": row.get("model_name"), "generated_at": row.get("generated_at").isoformat() if row.get("generated_at") else None})
    return result

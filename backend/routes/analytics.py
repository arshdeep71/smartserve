from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from functools import lru_cache

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi import Depends

from backend.database import database
from backend.services.security import require_roles
from ml.evaluate_models import evaluate as evaluate_feedback_model
from ml.forecast_demand import forecast_daily_demand
from ml.train_feedback_model import load_training_data, train_model

router = APIRouter(prefix="/api/businesses/{business_id}/analytics", tags=["analytics"])


def check_business(business_id):
    if not ObjectId.is_valid(business_id) or not database.businesses.find_one({"_id": ObjectId(business_id)}):
        raise HTTPException(status_code=404, detail="Business not found")


@router.get("/sales")
def sales_summary(business_id: str, user=Depends(require_roles("admin", "manager"))):
    check_business(business_id)
    orders = list(database.orders.find({"business_id": business_id, "status": "completed"}))
    by_item = {}
    for order in orders:
        for item in order["items"]:
            name = item["name"]
            by_item[name] = by_item.get(name, 0) + item["quantity"]
    return {
        "order_count": len(orders),
        "sales_total": round(sum(order["total"] for order in orders), 2),
        "items_sold": sorted(by_item.items(), key=lambda item: item[1], reverse=True),
    }


@lru_cache(maxsize=1)
def feedback_classifier():
    return train_model()


@lru_cache(maxsize=1)
def feedback_model_metrics():
    return evaluate_feedback_model()


@router.get("/feedback-insights")
def feedback_insights(business_id: str, user=Depends(require_roles("admin", "manager"))):
    check_business(business_id)
    training = load_training_data()
    model = feedback_classifier()
    metrics, _, _, repeats = feedback_model_metrics()
    rows = list(database.feedback.find({"business_id": business_id}).sort("submitted_at", -1))
    comments = [(row.get("comment") or "").strip() for row in rows]
    comment_indexes = [index for index, comment in enumerate(comments) if comment]
    predictions = []
    predicted_counts = Counter()

    if comment_indexes:
        texts = [comments[index] for index in comment_indexes]
        labels = model.predict(texts)
        probabilities = model.predict_proba(texts)
        for index, label, scores in zip(comment_indexes, labels, probabilities):
            row = rows[index]
            predicted_counts[str(label)] += 1
            predictions.append({
                "meal": row.get("meal", ""),
                "comment": comments[index],
                "predicted_label": str(label),
                "confidence": round(float(max(scores)), 3),
                "submitted_at": row["submitted_at"].isoformat() if row.get("submitted_at") else None,
            })

    return {
        "model": "character n-gram logistic regression",
        "training_examples": len(training),
        "training_labels": sorted(training["label"].unique().tolist()),
        "cross_validation": {
            "method": f"repeated stratified 3-fold cross-validation ({repeats} repeats)",
            "metrics": {
                name: {"mean": round(float(mean), 3), "std": round(float(std), 3)}
                for name, (mean, std) in metrics.items()
            },
        },
        "feedback_count": len(rows),
        "classified_count": len(predictions),
        "predicted_counts": sorted(predicted_counts.items(), key=lambda item: (-item[1], item[0])),
        "predictions": predictions,
        "warning": "Preliminary model trained on a small demonstration dataset; review predictions before acting on them.",
    }


@router.get("/demand-forecast")
def demand_forecast(business_id: str, user=Depends(require_roles("admin", "manager"))):
    check_business(business_id)
    rows = list(database.orders.find({"business_id": business_id, "status": "completed"}))
    quantities_by_day = defaultdict(lambda: defaultdict(int))
    for order in rows:
        created_at = order.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                continue
        if not isinstance(created_at, (datetime, date)):
            continue
        order_day = created_at.date() if isinstance(created_at, datetime) else created_at
        for item in order.get("items", []):
            name = item.get("name")
            quantity = item.get("quantity", 0)
            if name and isinstance(quantity, (int, float)) and quantity > 0:
                quantities_by_day[order_day][name] += quantity

    days = sorted(quantities_by_day)
    if len(days) < 2:
        return {
            "status": "insufficient_data",
            "method": "7-day moving average baseline",
            "observed_sales_days": len(days),
            "required_sales_days": 2,
            "message": "Complete sales on at least two different days to generate a demand estimate.",
        }

    latest_day = days[-1]
    start_day = latest_day - timedelta(days=6)
    window_days = [start_day + timedelta(days=offset) for offset in range(7)]
    recent_items = sorted({name for day in window_days for name in quantities_by_day.get(day, {})})
    per_item = []
    for name in recent_items:
        daily_values = [quantities_by_day.get(day, {}).get(name, 0) for day in window_days]
        per_item.append({"item": name, "estimated_quantity": round(sum(daily_values) / len(daily_values), 1)})

    total_per_day = [sum(quantities_by_day.get(day, {}).values()) for day in window_days]
    return {
        "status": "ready",
        "method": "7-day moving average baseline",
        "forecast_for": (latest_day + timedelta(days=1)).isoformat(),
        "window_start": start_day.isoformat(),
        "window_end": latest_day.isoformat(),
        "observed_sales_days": len(days),
        "estimated_total_quantity": forecast_daily_demand(total_per_day),
        "items": per_item,
        "warning": "A simple baseline estimate from completed orders, not a guarantee.",
    }

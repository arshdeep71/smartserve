from collections import Counter, defaultdict
from datetime import date
from functools import lru_cache

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi import Depends

from backend.database import database
from backend.services.security import require_roles
from backend.services.demand import existing_forecast, forecast_history, generate_forecast
from ml.evaluate_models import evaluate as evaluate_feedback_model
from ml.forecast_demand import forecast_daily_demand
from ml.train_feedback_model import load_training_data, train_model

router = APIRouter(prefix="/api/businesses/{business_id}/analytics", tags=["analytics"])

# Low-confidence predictions are surfaced for human review instead of being
# counted or presented as an assigned feedback category.
FEEDBACK_CONFIDENCE_THRESHOLD = 0.60


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
            confidence = float(max(scores))
            review_required = confidence < FEEDBACK_CONFIDENCE_THRESHOLD
            if not review_required:
                predicted_counts[str(label)] += 1
            predictions.append({
                "meal": row.get("meal", ""),
                "comment": comments[index],
                "predicted_label": None if review_required else str(label),
                "confidence": round(confidence, 3),
                "review_required": review_required,
                "review_reason": "Low model confidence; manual review required." if review_required else None,
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
        "classified_count": sum(not row["review_required"] for row in predictions),
        "review_required_count": sum(row["review_required"] for row in predictions),
        "confidence_threshold": FEEDBACK_CONFIDENCE_THRESHOLD,
        "predicted_counts": sorted(predicted_counts.items(), key=lambda item: (-item[1], item[0])),
        "predictions": predictions,
        "warning": "Experimental model trained on a small demonstration dataset. Low-confidence comments are left uncategorized for manual review; confidence is not a calibrated probability or a real-world accuracy guarantee.",
    }


@router.get("/demand-forecast")
def demand_forecast(business_id: str, user=Depends(require_roles("admin", "manager"))):
    check_business(business_id)
    from backend.services.demand import load_daily_sales
    daily = load_daily_sales(business_id)
    if daily.empty:
        return {"status": "insufficient_data", "message": "No completed sales yet.", "items": []}
    forecast_date = (max(daily.date) + __import__("datetime").timedelta(days=1)).isoformat()
    saved = existing_forecast(business_id, date.fromisoformat(forecast_date))
    if not saved:
        return {"status": "not_generated", "forecast_date": forecast_date, "message": "Forecast has not been generated yet. Use Generate Forecast or wait for the scheduled run.", "items": []}
    return {"status": "ready", "forecast_date": forecast_date, "generated_at": saved[0].get("generated_at").isoformat() if saved[0].get("generated_at") else None, "items": [{key:value for key,value in item.items() if key not in {"_id","business_id","evaluation"}} for item in saved], "evaluation": saved[0].get("evaluation"), "warning": "Predictions are estimates, not actual sales."}


@router.post("/demand-forecast/generate")
def generate_demand_forecast(business_id: str, user=Depends(require_roles("admin", "manager"))):
    check_business(business_id)
    return generate_forecast(business_id)


@router.get("/demand-forecast/history")
def demand_forecast_history(business_id: str, user=Depends(require_roles("admin", "manager"))):
    check_business(business_id)
    return forecast_history(business_id)

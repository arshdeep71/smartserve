"""Small non-blocking daily scheduler; Mongo's unique index is the final lock."""
import logging
import os
import threading
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from backend.database import database
from backend.services.demand import generate_forecast

logger = logging.getLogger("smartserve.forecast")
IST = ZoneInfo("Asia/Kolkata")
_thread = None
_stop = threading.Event()
_last_run_date = None


def run_daily_forecasts(target_date=None):
    businesses = list(database.businesses.find({}, {"_id": 1}))
    results = []
    for business in businesses:
        business_id = str(business["_id"])
        try:
            results.append((business_id, generate_forecast(business_id, target_date)))
        except Exception:
            logger.exception("Demand forecast failed for business %s", business_id)
    return results


def _scheduler_loop():
    global _last_run_date
    hour = int(os.getenv("DEMAND_FORECAST_HOUR", "18"))
    minute = int(os.getenv("DEMAND_FORECAST_MINUTE", "15"))
    interval = max(5, int(os.getenv("DEMAND_FORECAST_POLL_SECONDS", "30")))
    while not _stop.wait(interval):
        now = datetime.now(IST)
        if now.hour == hour and now.minute == minute and _last_run_date != now.date():
            _last_run_date = now.date()
            logger.info("Starting scheduled canteen forecasts for %s", now.date() + timedelta(days=1))
            run_daily_forecasts(now.date() + timedelta(days=1))


def start_scheduler():
    global _thread
    if os.getenv("DEMAND_FORECAST_SCHEDULER", "true").lower() not in {"1", "true", "yes", "on"}:
        logger.info("Demand forecast scheduler disabled by configuration")
        return
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_scheduler_loop, name="smartserve-demand-forecast", daemon=True)
    _thread.start()
    logger.info("Demand forecast scheduler started (Asia/Kolkata)")


def stop_scheduler():
    _stop.set()

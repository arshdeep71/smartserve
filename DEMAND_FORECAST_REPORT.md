# SmartServe demand forecast verification

## Data inspected

`data/sample_data.csv` contains 6 rows and 3 columns (`date`, `item`, `quantity`), spanning 2026-10-20 through 2026-10-25. It is demonstration data, not verified business history. Each row has a distinct date and item; there are no exact duplicate rows or nulls in this CSV. The rows do not form a complete item-by-day panel.

## Baseline evaluation

Executed with the project virtual environment: `.venv/Scripts/python.exe ml/evaluate_demand.py`.

- Chronological split in `ml/evaluate_demand.py`: first 4 of 6 daily totals for training (75%), last 2 for testing (25%).
- Baseline: mean of the up-to-4 training daily totals, held constant over the two test days.
- Actual recorded results: MAE **3.50**, R² **-0.0204081633**.
- RMSE/WAPE were not part of the old evaluator.

## New model evaluation

The new item-level pipeline requires at least 28 daily observations per item before it evaluates or selects trained models. The sample file provides only 6 dates, so it produced **0 supervised training rows**. Linear Regression and Random Forest were correctly withheld; no model scores are claimed. The app retains a labeled 7-day moving-average fallback when item history exists.

## Code and leakage notes

- `ml/demand_forecasting.py` aggregates completed orders by item and date, deduplicates stored orders by `order_id` in the Mongo service, and zero-fills each observed item's calendar span.
- Lag and rolling features are built from dates before each target date. Evaluation uses a chronological date cutoff; random shuffling is not used.
- Forecasts are stored in MongoDB `demand_forecasts`, uniquely keyed by business, item, and forecast date. Repeated generation preserves the first saved forecast.
- `backend/services/forecast_scheduler.py` checks a configurable local Asia/Kolkata time and delegates forecast generation to a daemon thread.
- Manual API: `POST /api/businesses/{business_id}/analytics/demand-forecast/generate`; retrieval: `GET .../demand-forecast`; comparisons: `GET .../demand-forecast/history`.

## Verification performed

- Python syntax compilation for the changed forecasting, route, scheduler, and startup modules: passed.
- Vite production build: passed.
- Existing baseline evaluator: passed with scores above.
- New pipeline on the actual sample CSV: returned `insufficient_data` (6 days, 0 supervised rows).

MongoDB forecast writes, duplicate-key behavior, scheduler timing, and a populated dashboard were not exercised against live business sales in this verification. A real demonstration is required to confirm those runtime behaviors. More genuine completed sales are needed before trained-model accuracy can be meaningfully evaluated.

## Model selection policy after final quality review

The production forecast path keeps the **7-day moving average (MA(7))** as its preferred method. Linear Regression and Random Forest remain experimental candidates and are not automatically promoted from a single chronological holdout. The separate synthetic experiment report records MA(7), MA(14), and other candidate results; MA(14)'s better synthetic rolling-period MAE makes it a candidate for later genuine-data validation only. The saved synthetic results are not evidence about real canteen performance.

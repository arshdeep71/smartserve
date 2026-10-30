"""Leakage-safe item-level demand features, evaluation, and prediction."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

MODEL_DIR = Path(__file__).resolve().parents[1] / "artifacts"
MODEL_PATH = MODEL_DIR / "demand_model.joblib"
MIN_DAYS = 28


def aggregate_orders(orders, start_date=None, end_date=None):
    """Aggregate completed order lines and fill zero-sales dates per item."""
    rows = []
    for order in orders:
        if order.get("status") != "completed":
            continue
        stamp = order.get("created_at")
        if isinstance(stamp, str):
            try:
                stamp = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            except ValueError:
                continue
        if not isinstance(stamp, (datetime, date)):
            continue
        day = stamp.date() if isinstance(stamp, datetime) else stamp
        for line in order.get("items", []):
            try:
                quantity = float(line.get("quantity"))
            except (TypeError, ValueError):
                continue
            if quantity < 0 or not np.isfinite(quantity):
                continue
            item_id = str(line.get("item_id") or line.get("menu_item_id") or line.get("name") or "")
            name = str(line.get("name") or "Unknown item")
            if item_id:
                rows.append((day, item_id, name, quantity))
    if not rows:
        return pd.DataFrame(columns=["date", "item_id", "item", "quantity"])
    raw = pd.DataFrame(rows, columns=["date", "item_id", "item", "quantity"])
    daily = raw.groupby(["date", "item_id", "item"], as_index=False, sort=True)["quantity"].sum()
    first = start_date or daily.date.min()
    last = end_date or daily.date.max()
    calendar = pd.date_range(first, last, freq="D").date
    result = []
    for (item_id, item), part in daily.groupby(["item_id", "item"]):
        values = part.set_index("date")["quantity"].reindex(calendar, fill_value=0)
        result.extend((day, item_id, item, float(qty)) for day, qty in values.items())
    return pd.DataFrame(result, columns=["date", "item_id", "item", "quantity"])


FEATURES = ["lag_1", "lag_2", "lag_3", "lag_7", "mean_7", "mean_14", "same_weekday", "trend_7", "weekday", "weekend", "item_code"]


def make_supervised(daily):
    """For each target day, calculate all demand features from prior days only."""
    if daily.empty:
        return pd.DataFrame(columns=[*FEATURES, "target", "date", "item_id", "item"])
    rows = []
    items = sorted(daily.item_id.unique())
    item_codes = {item: index for index, item in enumerate(items)}
    for (item_id, item), part in daily.groupby(["item_id", "item"]):
        part = part.sort_values("date").set_index("date")["quantity"]
        for day in part.index[14:]:
            history = part.loc[:day - timedelta(days=1)]
            if len(history) < 14:
                continue
            prior = [float(history.get(day - timedelta(days=lag), 0)) for lag in (1, 2, 3, 7)]
            last7 = [float(history.get(day - timedelta(days=offset), 0)) for offset in range(1, 8)]
            last14 = [float(history.get(day - timedelta(days=offset), 0)) for offset in range(1, 15)]
            weekday = day.weekday()
            rows.append({"lag_1":prior[0],"lag_2":prior[1],"lag_3":prior[2],"lag_7":prior[3],"mean_7":np.mean(last7),"mean_14":np.mean(last14),"same_weekday":prior[3],"trend_7":np.mean(last7[:3])-np.mean(last7[3:]),"weekday":weekday,"weekend":int(weekday>=5),"item_code":item_codes[item_id],"target":float(part.loc[day]),"date":day,"item_id":item_id,"item":item})
    return pd.DataFrame(rows)


def metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float); predicted = np.maximum(0, np.asarray(predicted, dtype=float))
    return {"mae":round(float(mean_absolute_error(actual,predicted)),4),"rmse":round(float(np.sqrt(mean_squared_error(actual,predicted))),4),"r2":round(float(r2_score(actual,predicted)),4) if len(actual)>1 else None,"wape":round(float(np.abs(actual-predicted).sum()/np.abs(actual).sum()),4) if np.abs(actual).sum() else None}


def evaluate_models(daily):
    samples = make_supervised(daily)
    if len(samples) < 20 or samples.date.nunique() < MIN_DAYS - 14:
        return {"status":"insufficient_data","days":int(daily.date.nunique()) if not daily.empty else 0,"samples":len(samples),"message":f"Need at least {MIN_DAYS} daily observations per item for chronological ML evaluation."}
    cut = samples.date.sort_values().unique()[max(1,int(samples.date.nunique()*.8))]
    train, test = samples[samples.date < cut], samples[samples.date >= cut]
    if len(train)<10 or test.empty:
        return {"status":"insufficient_data","days":int(daily.date.nunique()),"samples":len(samples),"message":"Not enough chronological train/test rows."}
    x_train, x_test = train[FEATURES], test[FEATURES]
    actual = test.target.to_numpy()
    baseline = test.mean_7.to_numpy()
    candidates={"7-day moving average":None,"Linear Regression":LinearRegression(),"Random Forest Regressor":RandomForestRegressor(n_estimators=150,min_samples_leaf=2,max_features=0.8,random_state=42,n_jobs=-1)}
    results={}
    for name,model in candidates.items():
        pred=baseline if model is None else model.fit(x_train,train.target).predict(x_test)
        results[name]={**metrics(actual,pred),"predictions":[{"date":row.date.isoformat(),"item":row.item,"actual":float(row.target),"predicted":round(float(max(0,p)),2)} for row,p in zip(test.itertuples(),pred)]}
    # Keep trained candidates experimental until genuine-history validation
    # supports a deliberate production promotion. MA(7) remains live by default.
    return {"status":"evaluated","training_rows":len(train),"testing_rows":len(test),"train_start":train.date.min().isoformat(),"train_end":train.date.max().isoformat(),"test_start":test.date.min().isoformat(),"test_end":test.date.max().isoformat(),"models":results,"selected_model":"7-day moving average","experimental_best_model":min(results,key=lambda name:results[name]["mae"]),"selection_policy":"7-day moving average remains preferred; trained candidates are experimental until validated on genuine sales history."}


def train_and_save(daily, evaluation):
    if evaluation.get("status") != "evaluated" or evaluation["selected_model"] == "7-day moving average":
        return None
    samples=make_supervised(daily)
    model=LinearRegression() if evaluation["selected_model"]=="Linear Regression" else RandomForestRegressor(n_estimators=150,min_samples_leaf=2,max_features=.8,random_state=42,n_jobs=-1)
    model.fit(samples[FEATURES],samples.target)
    MODEL_DIR.mkdir(exist_ok=True)
    import joblib
    joblib.dump({"model":model,"features":FEATURES,"name":evaluation["selected_model"],"version":"1.0"},MODEL_PATH)
    return MODEL_PATH


def predict_next(daily, evaluation=None):
    if daily.empty:
        return []
    latest=max(daily.date)
    target=latest+timedelta(days=1)
    samples=make_supervised(daily)
    evaluation=evaluation or {}
    model_obj=None
    if evaluation.get("status")=="evaluated" and evaluation.get("selected_model") not in (None,"7-day moving average"):
        train_and_save(daily,evaluation)
        import joblib
        model_obj=joblib.load(MODEL_PATH)
    result=[]
    for (item_id,item),part in daily.groupby(["item_id","item"]):
        part=part.sort_values("date").set_index("date").quantity
        history=[float(part.get(target-timedelta(days=n),0)) for n in range(1,15)]
        if len(part)<2: continue
        row={"lag_1":history[0],"lag_2":history[1],"lag_3":history[2],"lag_7":history[6],"mean_7":np.mean(history[:7]),"mean_14":np.mean(history),"same_weekday":history[6],"trend_7":np.mean(history[:3])-np.mean(history[3:7]),"weekday":target.weekday(),"weekend":int(target.weekday()>=5),"item_code":sorted(daily.item_id.unique()).index(item_id)}
        if model_obj:
            quantity=max(0,float(model_obj["model"].predict(pd.DataFrame([row],columns=FEATURES))[0])); name=model_obj["name"]; version=model_obj["version"]
        else:
            quantity=float(np.mean(history[:7])); name="7-day moving average"; version="baseline-1"
        result.append({"item_id":item_id,"item":item,"forecast_date":target.isoformat(),"predicted_quantity":round(quantity,1),"recent_average":round(float(np.mean(history[:7])),1),"previous_day_sales":history[0],"model_name":name,"model_version":version})
    return result

"""Independent, read-only validation of the saved synthetic demo experiments."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             mean_absolute_error, mean_squared_error, precision_score,
                             r2_score, recall_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

try:
    from .run_synthetic_demo_experiments import OUT, DATA, LABELS, NUMERIC_FEATURES, feature_rows, regression_metrics, svg_confusion
except ImportError:
    from run_synthetic_demo_experiments import OUT, DATA, LABELS, NUMERIC_FEATURES, feature_rows, regression_metrics, svg_confusion

STRESS = DATA / "feedback_stress_test.csv"
SEED = 20261030


def feedback_review():
    saved=json.loads((OUT/"results.json").read_text(encoding="utf-8"))
    train=pd.read_csv(DATA/"feedback_train.csv"); eval_data=pd.read_csv(DATA/"feedback_eval.csv"); stress=pd.read_csv(STRESS)
    model_path=OUT/"feedback_linear_svm_word.joblib"
    model=joblib.load(model_path)
    held_pred=model.predict(eval_data.comment)
    stress_pred=model.predict(stress.comment)
    expected=next(row for row in saved["feedback"]["results"] if row["model"]=="Linear SVM" and row["features"]=="word unigram+bigrams")
    all_model_metrics_match=True
    for row in saved["feedback"]["results"]:
        model_key=row["model"].lower().replace(" ","_")
        config_key="word" if row["features"].startswith("word") else "character"
        candidate=joblib.load(OUT/f"feedback_{model_key}_{config_key}.joblib")
        candidate_pred=candidate.predict(eval_data.comment)
        candidate_cm=confusion_matrix(eval_data.label,candidate_pred,labels=LABELS)
        candidate_metrics={"accuracy":float(accuracy_score(eval_data.label,candidate_pred)),"precision_macro":float(precision_score(eval_data.label,candidate_pred,average="macro",zero_division=0)),"recall_macro":float(recall_score(eval_data.label,candidate_pred,average="macro",zero_division=0)),"f1_macro":float(f1_score(eval_data.label,candidate_pred,average="macro",zero_division=0)),"f1_weighted":float(f1_score(eval_data.label,candidate_pred,average="weighted",zero_division=0))}
        all_model_metrics_match &= candidate_cm.tolist()==row["confusion_matrix"] and all(abs(candidate_metrics[key]-row[key])<1e-12 for key in candidate_metrics)
    if not all_model_metrics_match: raise AssertionError("One or more saved feedback models do not reproduce saved metrics")
    held_cm=confusion_matrix(eval_data.label,held_pred,labels=LABELS)
    held_metrics={"accuracy":float(accuracy_score(eval_data.label,held_pred)),"precision_macro":float(precision_score(eval_data.label,held_pred,average="macro",zero_division=0)),"recall_macro":float(recall_score(eval_data.label,held_pred,average="macro",zero_division=0)),"f1_macro":float(f1_score(eval_data.label,held_pred,average="macro",zero_division=0)),"f1_weighted":float(f1_score(eval_data.label,held_pred,average="weighted",zero_division=0))}
    if held_cm.tolist()!=expected["confusion_matrix"]: raise AssertionError("Saved SVM model does not reproduce recorded evaluation confusion matrix")
    if not set(train.comment).isdisjoint(eval_data.comment) or not set(train.comment).isdisjoint(stress.comment) or not set(eval_data.comment).isdisjoint(stress.comment): raise AssertionError("Feedback texts overlap across training/evaluation/stress partitions")
    cm=confusion_matrix(stress.label,stress_pred,labels=LABELS)
    (OUT/"feedback_stress_confusion_matrix.svg").write_text(svg_confusion(cm,LABELS),encoding="utf-8")
    metrics={"accuracy":float(accuracy_score(stress.label,stress_pred)),"precision_macro":float(precision_score(stress.label,stress_pred,average="macro",zero_division=0)),"recall_macro":float(recall_score(stress.label,stress_pred,average="macro",zero_division=0)),"f1_macro":float(f1_score(stress.label,stress_pred,average="macro",zero_division=0)),"f1_weighted":float(f1_score(stress.label,stress_pred,average="weighted",zero_division=0))}
    stress_out=stress.copy(); stress_out["predicted_label"]=stress_pred
    stress_out.to_csv(OUT/"feedback_stress_predictions.csv",index=False)
    return {"training_rows":len(train),"heldout_rows":len(eval_data),"stress_rows":len(stress),"stress_classes":stress.label.value_counts().to_dict(),"stress_languages":stress.language.value_counts().to_dict(),"train_eval_stress_text_overlap":0,"all_six_saved_models_reproduce_saved_metrics":bool(all_model_metrics_match),"heldout_reproduces_saved_matrix":True,"heldout_metrics":held_metrics,"heldout_metrics_match_results_json":all(abs(held_metrics[key]-expected[key])<1e-12 for key in held_metrics),"stress_metrics":metrics,"stress_confusion_matrix":cm.tolist(),"best_saved_macro_f1":expected["f1_macro"],"stress_ambiguous_count":int(stress.stress_type.str.contains("ambiguous").sum()),"misspelling_examples_count":int(stress.stress_type.str.contains("misspell").sum())}


def metrics_by_item(frame, actual_col, pred_col):
    result={}
    for item,part in frame.groupby("item"):
        actual=part[actual_col].to_numpy(float); pred=part[pred_col].to_numpy(float)
        result[item]={"n":len(part),"mae":float(mean_absolute_error(actual,pred)),"rmse":float(np.sqrt(mean_squared_error(actual,pred))),"wape":float(np.abs(actual-pred).sum()/np.abs(actual).sum())}
    return result


def make_features(all_sales):
    all_sales=all_sales.copy(); all_sales["date"]=pd.to_datetime(all_sales.date).dt.date
    rows=[]
    for (item_id,item),part in all_sales.sort_values("date").groupby(["item_id","item"]):
        series=part.set_index("date").quantity.astype(float)
        first=min(series.index)
        for day,target in series.items():
            if (day-first).days<14: continue
            prior=[float(series.get(day-pd.Timedelta(days=k),0)) for k in range(1,15)]
            rows.append({"date":day,"item_id":item_id,"item":item,"target":float(target),"lag_1":prior[0],"lag_2":prior[1],"lag_3":prior[2],"lag_7":prior[6],"mean_7":float(np.mean(prior[:7])),"mean_14":float(np.mean(prior)),"weekday":day.weekday(),"weekend":int(day.weekday()>=5),"trend_7":float(np.mean(prior[:3])-np.mean(prior[3:7])),"mean_3":float(np.mean(prior[:3])),"baseline_7":float(np.mean(prior[:7])),"baseline_14":float(np.mean(prior)),"seasonal_naive":prior[6]})
    return pd.DataFrame(rows)


def evaluate_demand_period(features, eval_start, eval_end):
    train=features[features.date<eval_start]
    test=features[(features.date>=eval_start)&(features.date<=eval_end)]
    xcols=NUMERIC_FEATURES+["item_id"]
    pre=ColumnTransformer([("item",OneHotEncoder(handle_unknown="ignore"),["item_id"]),("num",Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())]),NUMERIC_FEATURES)])
    estimators={"Linear Regression":LinearRegression(),"Random Forest":RandomForestRegressor(n_estimators=200,min_samples_leaf=2,random_state=SEED,n_jobs=-1)}
    preds={"MA-3":test.mean_3.to_numpy(),"MA-7":test.baseline_7.to_numpy(),"MA-14":test.baseline_14.to_numpy(),"Seasonal Naive (lag 7)":test.seasonal_naive.to_numpy()}
    for name,estimator in estimators.items():
        model=Pipeline([("features",pre),("model",estimator)])
        model.fit(train[xcols],train.target)
        preds[name]=model.predict(test[xcols])
    actual=test.target.to_numpy()
    return test,preds,{name:regression_metrics(actual,pred) for name,pred in preds.items()}


def demand_review():
    saved=json.loads((OUT/"results.json").read_text(encoding="utf-8"))
    actual_pred=pd.read_csv(OUT/"demand_actual_vs_predicted.csv")
    recomputed={}
    for name in ("Moving Average","Linear Regression","Random Forest"):
        recomputed[name]=regression_metrics(actual_pred.actual,actual_pred[name])
        for metric,value in recomputed[name].items():
            if abs(value-saved["demand"]["metrics"][name][metric])>1e-10: raise AssertionError(f"Saved {name} {metric} does not match actual-vs-predicted CSV")
    per_item={name:metrics_by_item(actual_pred,"actual",name) for name in ("Moving Average","Linear Regression","Random Forest")}
    train=pd.read_csv(DATA/"sales_train.csv",parse_dates=["date"]); test=pd.read_csv(DATA/"sales_eval.csv",parse_dates=["date"])
    all_sales=pd.concat([train,test],ignore_index=True)
    feats=make_features(all_sales)
    # Three non-overlapping 18-day rolling-origin windows, each trained only on earlier target dates.
    dates=sorted(all_sales.date.unique())
    periods=[]
    for first_index,last_index in ((36,54),(54,72),(72,90)):
        start=pd.Timestamp(dates[first_index]).date(); end=pd.Timestamp(dates[last_index-1]).date()
        frame,preds,metrics=evaluate_demand_period(feats,start,end)
        perperiod={name:metrics_by_item(frame.assign(**{f"pred_{i}":pred for i,(name,pred) in enumerate(preds.items())}),"target",f"pred_{i}") for i,name in enumerate(preds)}
        periods.append({"start":start.isoformat(),"end":end.isoformat(),"train_rows":int((feats.date<start).sum()),"eval_rows":len(frame),"metrics":metrics,"per_item":perperiod})
    main_item={row["item"]:row for row in actual_pred.drop_duplicates("item").to_dict("records")}
    return {"saved_metrics_recomputed_from_actual_prediction_csv":recomputed,"metrics_match_results_json":True,"per_item_main_holdout":per_item,"chronological_periods":periods,"moving_average_best_periods":sum(min(p["metrics"],key=lambda k:p["metrics"][k]["mae"]).startswith("MA-") for p in periods),"models_are_isolated_under_demo_artifact_path":str(OUT).endswith("synthetic_demo_experiments"),"chart_exists_and_labeled":(OUT/"demand_forecast_comparison.svg").exists() and "SYNTHETIC DEMO" in (OUT/"demand_forecast_comparison.svg").read_text(encoding="utf-8"),"confusion_matrix_svg_files":len(list(OUT.glob("feedback_*_confusion_matrix.svg")))}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={"title":"FINAL QUALITY REVIEW — SYNTHETIC DEMO ONLY","feedback":feedback_review(),"demand":demand_review()}
    (OUT/"quality_review.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__": main()

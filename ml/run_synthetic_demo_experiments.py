"""Run isolated ML experiments on data/synthetic_demo files only.

All artifacts are written under artifacts/synthetic_demo_experiments and never
overwrite production model artifacts or read MongoDB.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             mean_absolute_error, mean_squared_error,
                             precision_score, r2_score, recall_score)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestRegressor

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "synthetic_demo"
OUT = ROOT / "artifacts" / "synthetic_demo_experiments"
SEED = 20261030
LABELS = ["positive", "spice", "quality"]


def svg_confusion(matrix, labels):
    cell, left, top = 88, 135, 90
    width, height = left + cell * len(labels) + 30, top + cell * len(labels) + 60
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="20" y="30" font-family="Arial" font-size="18" font-weight="bold">Synthetic demo confusion matrix</text>',
             '<text x="12" y="65" font-family="Arial" font-size="12">Rows: actual · Columns: predicted</text>']
    for j, label in enumerate(labels):
        x = left + j * cell + cell / 2
        parts.append(f'<text x="{x}" y="{top-12}" text-anchor="middle" font-family="Arial" font-size="12">{label}</text>')
        y = top + j * cell + cell / 2
        parts.append(f'<text x="{left-12}" y="{y}" text-anchor="end" dominant-baseline="middle" font-family="Arial" font-size="12">{label}</text>')
    maximum = max(1, int(np.max(matrix)))
    for i in range(len(labels)):
        for j in range(len(labels)):
            x, y, value = left + j * cell, top + i * cell, int(matrix[i, j])
            shade = 245 - int(130 * value / maximum)
            parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="rgb({shade},{shade},{shade})" stroke="white"/>')
            parts.append(f'<text x="{x+cell/2}" y="{y+cell/2}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="22">{value}</text>')
    parts.append('</svg>')
    return ''.join(parts)


def svg_forecast(rows):
    width, height, left, top, right, bottom = 1100, 480, 70, 55, 30, 75
    plot_w, plot_h = width-left-right, height-top-bottom
    values = [row[k] for row in rows for k in ("actual", "Moving Average", "Linear Regression", "Random Forest")]
    max_y = max(values) * 1.12 or 1
    n = len(rows)
    x = lambda i: left + (plot_w * i / max(1, n-1))
    y = lambda v: top + plot_h * (1-v/max_y)
    colors = {"actual":"#202020", "Moving Average":"#e09f3e", "Linear Regression":"#335cbb", "Random Forest":"#2a9d68"}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">','<rect width="100%" height="100%" fill="white"/>','<text x="20" y="28" font-family="Arial" font-size="18" font-weight="bold">SYNTHETIC DEMO — actual versus forecast</text>']
    for step in range(5):
        val = max_y*step/4
        yy = y(val)
        parts += [f'<line x1="{left}" y1="{yy}" x2="{width-right}" y2="{yy}" stroke="#ddd"/>', f'<text x="{left-8}" y="{yy+4}" text-anchor="end" font-family="Arial" font-size="11">{val:.0f}</text>']
    for key, color in colors.items():
        coords = ' '.join(f'{x(i):.1f},{y(float(row[key])):.1f}' for i,row in enumerate(rows))
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{coords}"/>')
    for index,(key,color) in enumerate(colors.items()):
        xx=left+index*230
        parts += [f'<line x1="{xx}" y1="{height-30}" x2="{xx+25}" y2="{height-30}" stroke="{color}" stroke-width="3"/>',f'<text x="{xx+32}" y="{height-26}" font-family="Arial" font-size="12">{key}</text>']
    parts.append('</svg>')
    return ''.join(parts)


def feedback_experiments():
    train = pd.read_csv(DATA / "feedback_train.csv")
    test = pd.read_csv(DATA / "feedback_eval.csv")
    assert set(train.source) == set(test.source) == {"synthetic_demo"}
    assert train.is_synthetic.eq(True).all() and test.is_synthetic.eq(True).all()
    assert set(train.split) == {"train"} and set(test.split) == {"eval"}
    assert not set(train.comment) & set(test.comment), "Feedback comments overlap between splits"
    assert train.drop(columns=["split"]).duplicated().sum() == 0
    assert test.drop(columns=["split"]).duplicated().sum() == 0
    assert not train.isna().any().any() and not test.isna().any().any()
    configs = {
        "word unigram+bigrams": TfidfVectorizer(analyzer="word", ngram_range=(1,2), min_df=1, sublinear_tf=True),
        "character 2-5 grams": TfidfVectorizer(analyzer="char_wb", ngram_range=(2,5), min_df=1, sublinear_tf=True),
    }
    classifiers = {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=SEED),
        "Linear SVM": LinearSVC(random_state=SEED),
        "Multinomial Naive Bayes": MultinomialNB(),
    }
    results, best_f1 = [], -1
    y_train, y_test = train.label, test.label
    for config_name, vectorizer in configs.items():
        for model_name, classifier in classifiers.items():
            model = make_pipeline(vectorizer, classifier)
            model.fit(train.comment, y_train)
            pred = model.predict(test.comment)
            matrix = confusion_matrix(y_test, pred, labels=LABELS)
            row = {"model": model_name, "features": config_name,
                   "accuracy": float(accuracy_score(y_test,pred)),
                   "precision_macro": float(precision_score(y_test,pred,average="macro",zero_division=0)),
                   "recall_macro": float(recall_score(y_test,pred,average="macro",zero_division=0)),
                   "f1_macro": float(f1_score(y_test,pred,average="macro",zero_division=0)),
                   "f1_weighted": float(f1_score(y_test,pred,average="weighted",zero_division=0)),
                   "confusion_matrix": matrix.tolist()}
            results.append(row)
            filename = f"feedback_{model_name.lower().replace(' ','_')}_{config_name.split()[0]}.joblib"
            joblib.dump(model, OUT / filename)
            matrix_name = filename.removesuffix(".joblib") + "_confusion_matrix.svg"
            (OUT / matrix_name).write_text(svg_confusion(matrix,LABELS),encoding="utf-8")
            if row["f1_macro"] > best_f1:
                best_f1, best = row["f1_macro"], row
                (OUT / "feedback_confusion_matrix.svg").write_text(svg_confusion(matrix,LABELS),encoding="utf-8")
    return {"train_rows":len(train),"eval_rows":len(test),"train_classes":train.label.value_counts().to_dict(),"eval_classes":test.label.value_counts().to_dict(),"train_duplicates":int(train.comment.duplicated().sum()),"eval_duplicates":int(test.comment.duplicated().sum()),"train_eval_overlap":0,"results":results,"best_by_macro_f1":{"model":best["model"],"features":best["features"],"macro_f1":best["f1_macro"]}}


NUMERIC_FEATURES = ["lag_1","lag_2","lag_3","lag_7","mean_7","mean_14","weekday","weekend","trend_7"]


def feature_rows(train, test):
    combined = pd.concat([train.assign(_split="train"),test.assign(_split="eval")],ignore_index=True)
    combined["date"] = pd.to_datetime(combined.date).dt.date
    result=[]
    for (item_id,item), part in combined.sort_values("date").groupby(["item_id","item"]):
        series=part.set_index("date").quantity.astype(float)
        split_dates=set(pd.to_datetime(train.date).dt.date)
        for day, target in series.items():
            prior=[float(series.get(day-pd.Timedelta(days=k),0)) for k in range(1,15)]
            if (day in split_dates and (day - min(series.index)).days < 14):
                continue
            if (day not in split_dates and (day - min(series.index)).days < 14):
                continue
            weekday=day.weekday()
            row={"date":day,"item_id":item_id,"item":item,"target":float(target),"lag_1":prior[0],"lag_2":prior[1],"lag_3":prior[2],"lag_7":prior[6],"mean_7":float(np.mean(prior[:7])),"mean_14":float(np.mean(prior)),"weekday":weekday,"weekend":int(weekday>=5),"trend_7":float(np.mean(prior[:3])-np.mean(prior[3:7])),"baseline":float(np.mean(prior[:7])),"split":"train" if day in split_dates else "eval"}
            result.append(row)
    return pd.DataFrame(result)


def regression_metrics(actual,predicted):
    actual=np.asarray(actual,float); predicted=np.maximum(0,np.asarray(predicted,float))
    return {"mae":float(mean_absolute_error(actual,predicted)),"rmse":float(np.sqrt(mean_squared_error(actual,predicted))),"r2":float(r2_score(actual,predicted)),"wape":float(np.abs(actual-predicted).sum()/np.abs(actual).sum()) if np.abs(actual).sum() else None}


def demand_experiments():
    train=pd.read_csv(DATA/"sales_train.csv",parse_dates=["date"])
    test=pd.read_csv(DATA/"sales_eval.csv",parse_dates=["date"])
    assert train.source.eq("synthetic_demo").all() and test.source.eq("synthetic_demo").all()
    assert train.is_synthetic.eq(True).all() and test.is_synthetic.eq(True).all()
    train_dates=set(train.date.dt.date); test_dates=set(test.date.dt.date)
    assert train_dates and test_dates and max(train_dates)<min(test_dates), "Sales date split overlaps or is not chronological"
    assert train.duplicated(["date","item_id"]).sum()==0 and test.duplicated(["date","item_id"]).sum()==0
    assert not train.isna().any().any() and not test.isna().any().any()
    features=feature_rows(train,test)
    tr=features[features.split.eq("train")].copy(); ev=features[features.split.eq("eval")].copy()
    if tr.empty or ev.empty: raise ValueError("Not enough ordered history after lags for a valid evaluation")
    pre=ColumnTransformer([("item",OneHotEncoder(handle_unknown="ignore"),["item_id"]),("numeric",Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())]),NUMERIC_FEATURES)])
    models={"Linear Regression":LinearRegression(),"Random Forest":RandomForestRegressor(n_estimators=200,min_samples_leaf=2,random_state=SEED,n_jobs=-1)}
    predictions={"Moving Average":ev.baseline.to_numpy()}
    fitted={}
    for name,estimator in models.items():
        pipe=Pipeline([("features",pre),("model",estimator)])
        pipe.fit(tr[NUMERIC_FEATURES+['item_id']],tr.target)
        predictions[name]=pipe.predict(ev[NUMERIC_FEATURES+['item_id']])
        fitted[name]=pipe
    actual=ev.target.to_numpy()
    results={name:regression_metrics(actual,pred) for name,pred in predictions.items()}
    rows=[]
    for i,(_,r) in enumerate(ev.reset_index(drop=True).iterrows()):
        rows.append({"date":r["date"].isoformat(),"item_id":r["item_id"],"item":r["item"],"actual":float(r.target),**{name:float(max(0,pred[i])) for name,pred in predictions.items()}})
    # Preserve the held-out period in a compact actual/prediction output table.
    pd.DataFrame(rows).to_csv(OUT/"demand_actual_vs_predicted.csv",index=False)
    (OUT/"demand_forecast_comparison.svg").write_text(svg_forecast(rows),encoding="utf-8")
    for name,pipe in fitted.items():
        joblib.dump(pipe,OUT/f"demand_{name.lower().replace(' ','_')}.joblib")
    return {"train_rows":len(train),"eval_rows":len(test),"train_item_days":len(tr),"eval_item_days":len(ev),"train_date_start":min(train_dates).isoformat(),"train_date_end":max(train_dates).isoformat(),"eval_date_start":min(test_dates).isoformat(),"eval_date_end":max(test_dates).isoformat(),"date_overlap":len(train_dates & test_dates),"train_duplicates":int(train.duplicated(["date","item_id"]).sum()),"eval_duplicates":int(test.duplicated(["date","item_id"]).sum()),"items":sorted(train.item.unique()),"metrics":results,"actual_vs_predicted":rows}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    feedback=feedback_experiments()
    demand=demand_experiments()
    result={"label":"SYNTHETIC DEMO EVALUATION — NOT REAL CANTEEN PERFORMANCE","seed":SEED,"feedback":feedback,"demand":demand}
    (OUT/"results.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()

# Final ML quality review — SmartServe

## Scope and provenance

**SYNTHETIC DEMO EVALUATION ONLY — NOT REAL CANTEEN PERFORMANCE.** This review used the generated feedback and sales files under `data/synthetic_demo/` only. It did not read MongoDB or production datasets. The feedback classifier evaluated on the original held-out synthetic split was loaded from `feedback_linear_svm_word.joblib` and not retrained or tuned for the stress test. Demand model settings were held fixed from the previous experiment. Artifacts remain under `artifacts/synthetic_demo_experiments/`, separate from production model paths.

## Feedback audit

### Generator leakage review

The earlier perfect score needed scrutiny. The first generator version embedded a row number in each comment while assigning classes in a repeating order. That created a direct label-correlated identifier. We removed the row-number suffix and regenerated both splits using the same seed before the saved 1.0000 result. The current files have no row number, comment ID, split name, or label field embedded in the comment text. Training/evaluation/stress comments have zero exact text overlap; CSV metadata contains `label`, `split`, `source`, and `is_synthetic` outside the text feature.

There is still **generator-template dependence**: original train/evaluation text was sampled from the same small set of class-specific phrases and sentence frames. They are disjoint samples, but not independently authored real-world comments. This makes the 30-comment holdout too easy and explains why its perfect score should not be generalized.

### Frozen classifier stress test

The saved Linear SVM + word unigram/bigram TF-IDF was applied unchanged to 39 manually written stress examples: 22 English, 17 Hinglish; 7 mixed/ambiguous, 2 misspelled, and examples of very short and informal comments. No stress examples were used for fitting or tuning.

| Metric | Original held-out synthetic set (30) | Independent stress set (39) |
|---|---:|---:|
| Accuracy | 1.0000 | 0.5385 |
| Macro precision | 1.0000 | 0.6467 |
| Macro recall | 1.0000 | 0.5440 |
| Macro F1 | 1.0000 | 0.5364 |
| Weighted F1 | 1.0000 | 0.5286 |

Stress-set confusion matrix (actual rows, predicted columns; order: positive, spice, quality):

```text
             predicted
actual       positive  spice  quality
positive         11       0       2
spice             4       6       2
quality          10       0       4
```

The largest issue is quality comments predicted as positive, and many spice comments predicted positive. This stress set is small and manually labeled, but it exposes a clear robustness gap. Short comments, mixed sentiment, misspellings, and Hinglish are not handled reliably by the current demo classifier.

## Demand metric verification

Metrics below were independently recomputed from `demand_actual_vs_predicted.csv` and matched `results.json` within floating-point tolerance.

| Model | MAE | RMSE | R² | WAPE |
|---|---:|---:|---:|---:|
| Existing 7-day moving average | 3.1825 | 3.8908 | 0.6616 | 0.0949 |
| Linear Regression | 3.3963 | 4.0740 | 0.6289 | 0.1013 |
| Random Forest | 3.4530 | 4.0885 | 0.6263 | 0.1030 |

The 7-day baseline beats both trained models on all four aggregate metrics in the final 18-day holdout.

### Per-item final holdout MAE

| Synthetic food item | MA(7) | Linear Regression | Random Forest |
|---|---:|---:|---:|
| DEMO Chana Chawal | 2.8333 | 2.9002 | 2.7760 |
| DEMO Dal Roti | 3.0873 | 3.6010 | 3.5952 |
| DEMO Rajma Chawal | 3.6270 | 3.6877 | 3.9879 |

Random Forest is slightly better for Chana Chawal only; both regressors are worse for the other two items.

## Chronological robustness and baseline windows

Three non-overlapping rolling-origin evaluation periods were used. Each period trains only on earlier dates and tests on the next 18 days. Table values are MAE; lower is better.

| Evaluation dates | MA(3) | MA(7) | MA(14) | Seasonal naive (lag 7) | Linear Regression | Random Forest |
|---|---:|---:|---:|---:|---:|---:|
| 2026-09-07–2026-09-24 | 4.0556 | 3.2407 | **3.0370** | 3.2963 | 3.8313 | 3.1016 |
| 2026-09-25–2026-10-12 | 3.1049 | 2.5026 | **2.3307** | 3.2037 | 3.0217 | 2.9028 |
| 2026-10-13–2026-10-30 | 3.5185 | 3.1825 | **3.1045** | 4.2778 | 3.3963 | 3.4530 |

MA(14) has the lowest MAE in all three synthetic periods. On this generated series, a longer moving average smooths the seeded day-to-day random variation. Seasonal naive is worst in two periods and does not reliably capture the synthetic series. The small, smoothly generated data does not justify replacing the simple moving-average family with a trained regressor. Keep the moving-average method as preferred; if selecting a demo window, MA(14) is the observed synthetic winner, subject to validation on genuine history.

## Why the trained regressors trail

The generator produces relatively smooth demand with only a mild trend and weekend multiplier plus random noise. The lag and calendar features offer limited extra signal; Linear Regression can extrapolate the artificial trend poorly, and Random Forest tends to smooth/predict toward learned averages. Moving averages suppress much of the generated noise. This is an explanation consistent with the data-generation code, not a claim about real canteen demand.

## Artifact checks

- Saved Linear SVM reproduces the recorded held-out confusion matrix and scores.
- All six feedback model/config confusion-matrix SVGs exist; the stress confusion-matrix SVG was generated separately.
- Forecast comparison SVG exists and is explicitly labeled synthetic demo; actual/predicted CSV reproduces the saved aggregate scores.
- Demo model files are confined to `artifacts/synthetic_demo_experiments/`; none use or overwrite the production `artifacts/demand_model.joblib` path.
- Numeric result details, three-period metrics, per-item results, and stress predictions are in `quality_review.json` and `feedback_stress_predictions.csv`.

## Recommendation and limitations

Treat the perfect original feedback score as a generator-template result, not a model-quality claim. The stress test indicates substantial domain and language robustness problems. Collect consented real comments from diverse students, manually label them, and retain an untouched real-world stress/temporal test set.

For demand, keep a moving-average baseline. Collect many months of genuine completed item-level transactions, include zero-sale days and menu changes, then repeat rolling-origin tests across seasons and compare by item. No reported score in this report represents real SmartServe customer or canteen performance.

## Implementation cleanup and current selection policy

- The SVM remains isolated to the synthetic experiment artifacts. The production feedback insight route continues to use its existing Logistic Regression model and MongoDB feedback records; it does not load the demo SVM.
- Production feedback suggestions now abstain when the existing classifier's top `predict_proba` score is below **0.60**. The API returns `predicted_label: null`, `review_required: true`, and a review reason; the dashboard displays “Manual review” and excludes these records from category counts. This is a conservative triage rule, not calibrated uncertainty: confidence values have not been calibrated, and real feedback validation is still required.
- MA(7) is pinned as the live forecast method. Linear Regression and Random Forest metrics remain experimental comparisons. MA(14) remains an experimental candidate based only on synthetic rolling-origin periods; it is not selected or promoted automatically.
- Forecast generation, MongoDB persistence and uniqueness, scheduler, and dashboard routes remain in place. This cleanup did not exercise live MongoDB writes or scheduler timing.

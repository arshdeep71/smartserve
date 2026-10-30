# SYNTHETIC DEMO EVALUATION — NOT REAL CANTEEN PERFORMANCE

Run with `.venv/Scripts/python.exe ml/run_synthetic_demo_experiments.py`. Random seed: `20261030`. All inputs came only from `data/synthetic_demo/`; MongoDB and the non-demo datasets were not read. Trained demo pipelines are saved in this directory, separate from production artifacts.

## Split and integrity checks

- Feedback: 120 training comments (40 per class), 30 held-out comments (10 per class); zero duplicate comments within either split and zero train/eval comment overlap.
- Sales: train is 2026-08-02 through 2026-10-12 (72 dates, 216 item-day rows); evaluation is 2026-10-13 through 2026-10-30 (18 dates, 54 item-day rows). Date overlap: zero. Duplicate date/item rows: zero.
- Demand features use only earlier dates: lags 1/2/3/7, past 7/14-day means, weekday/weekend, and recent 3-versus-4-day trend. Evaluation is rolling-origin: each later evaluation date can use actual values from dates that precede it, never the target date or future dates.
- The generator previously placed a row number in feedback text, correlated with the label. That accidental target clue was removed, and the same seeded demo files were regenerated before these results were produced.

## Feedback classification (30 held-out synthetic comments)

| Model | TF-IDF | Accuracy | Macro precision | Macro recall | Macro F1 | Weighted F1 | Confusion matrix (actual rows, predicted columns: positive, spice, quality) |
|---|---|---:|---:|---:|---:|---:|---|
| Logistic Regression | word 1–2 grams | 0.9667 | 0.9697 | 0.9667 | 0.9666 | 0.9666 | `[[10,0,0],[0,10,0],[1,0,9]]` |
| Linear SVM | word 1–2 grams | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | `[[10,0,0],[0,10,0],[0,0,10]]` |
| Multinomial Naive Bayes | word 1–2 grams | 0.9667 | 0.9697 | 0.9667 | 0.9666 | 0.9666 | `[[10,0,0],[0,10,0],[1,0,9]]` |
| Logistic Regression | char 2–5 grams | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | `[[10,0,0],[0,10,0],[0,0,10]]` |
| Linear SVM | char 2–5 grams | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | `[[10,0,0],[0,10,0],[0,0,10]]` |
| Multinomial Naive Bayes | char 2–5 grams | 0.9000 | 0.9024 | 0.9000 | 0.8997 | 0.8997 | `[[8,0,2],[0,10,0],[1,0,9]]` |

Best experimental result by macro F1 is Linear SVM with word unigram/bigram TF-IDF (1.0000 on this generated holdout). The independent stress-set macro F1 is 0.5364 (see `FINAL_ML_QUALITY_REVIEW.md`). The SVM remains an experimental classifier only; neither score is real-world accuracy, and this result does not establish production readiness. The existing feedback collection and production model workflow remain unchanged.

Confusion matrix SVGs were generated for all six configurations in this directory.

## Demand forecasting (54 held-out synthetic item-days)

| Model | MAE | RMSE | R² | WAPE | Versus moving-average baseline |
|---|---:|---:|---:|---:|---|
| Moving Average (past 7-day mean) | 3.1825 | 3.8908 | 0.6616 | 0.0949 | Baseline |
| Linear Regression | 3.3963 | 4.0740 | 0.6289 | 0.1013 | Worse on all four metrics |
| Random Forest | 3.4530 | 4.0885 | 0.6263 | 0.1030 | Worse on all four metrics |

The simple moving-average baseline wins on this synthetic chronological holdout. The trained regressors did not improve over it. The generated forecast series is stored in `demand_actual_vs_predicted.csv`; the SVG comparison chart is `demand_forecast_comparison.svg`.

MA(7) remains the current preferred production method. MA(14) is only an experimental candidate: it has the lowest MAE in the three generated rolling periods, but this synthetic result does not justify an automatic live promotion. Linear Regression and Random Forest are likewise comparison candidates only until genuine sales history demonstrates stable improvement.

## Limitations

The generator creates simple, low-noise, repeated language patterns and a smooth sales series. The held-out data is generated from the same rules as training. These metrics demonstrate that the experiment pipeline runs and that models can be compared; they do not estimate performance on actual students or canteen sales. Validate later with a larger, independently collected, consented, real dataset. Keep an untouched temporal test period and compare against the baseline.

"""Evaluate a simple demand baseline with chronological held-out days."""
from sklearn.metrics import mean_absolute_error, r2_score

from prepare_data import load_sales


def evaluate():
    sales = load_sales().sort_values("date")
    daily = sales.groupby("date")["quantity"].sum()
    if len(daily) < 4:
        raise ValueError("At least four dates are needed for demand evaluation")
    split = max(2, int(len(daily) * 0.75))
    train, test = daily.iloc[:split], daily.iloc[split:]
    baseline = float(train.tail(min(7, len(train))).mean())
    predictions = [baseline] * len(test)
    return mean_absolute_error(test, predictions), r2_score(test, predictions) if len(test) > 1 else None


if __name__ == "__main__":
    mae, r_squared = evaluate()
    print(f"MAE: {mae:.2f}\nR²: {r_squared if r_squared is not None else 'requires multiple test days'}")

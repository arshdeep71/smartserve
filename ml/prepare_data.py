"""Load and validate the demonstration sales data."""
from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "sample_data.csv"


def load_sales():
    sales = pd.read_csv(DATA_FILE, parse_dates=["date"])
    sales["quantity"] = pd.to_numeric(sales["quantity"], errors="raise")
    if sales.empty or (sales["quantity"] < 0).any():
        raise ValueError("Sales data must contain non-negative quantities")
    return sales


if __name__ == "__main__":
    print(load_sales().to_string(index=False))

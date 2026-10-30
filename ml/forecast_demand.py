"""Create a simple next-day demand estimate from historical quantities."""
try:  # Support both script execution and imports from the API.
    from .prepare_data import load_sales
except ImportError:
    from prepare_data import load_sales


def forecast_next_day():
    sales = load_sales()
    daily = sales.groupby("date")["quantity"].sum().sort_index()
    return forecast_daily_demand(daily.tolist())


def forecast_daily_demand(daily_quantities, window=7):
    """Forecast total demand with a recent daily-mean baseline."""
    quantities = [float(quantity) for quantity in daily_quantities]
    if len(quantities) < 2:
        raise ValueError("At least two days of sales are needed for a baseline forecast")
    recent = quantities[-window:]
    return round(sum(recent) / len(recent), 1)


if __name__ == "__main__":
    print(f"Estimated next-day quantity: {forecast_next_day()}")

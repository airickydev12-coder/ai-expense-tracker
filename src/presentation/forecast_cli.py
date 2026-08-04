from src.financial.forecasting.service import (
    build_current_financial_forecast,
)
from src.presentation.cli_context import get_cli_user_id
from src.presentation.views import (
    display_financial_forecast,
)


def select_forecast_horizon() -> int | None:
    """Prompt for a supported forecasting horizon."""
    print("\nForecast Horizons")
    print("1. 30 days")
    print("2. 90 days")
    print("3. 365 days")
    print("4. Back")

    selection = input("Choose a forecast horizon: ").strip()

    horizons = {
        "1": 30,
        "2": 90,
        "3": 365,
    }

    if selection == "4":
        return None

    horizon = horizons.get(selection)

    if horizon is None:
        print("Invalid forecast option. " "Please choose 1, 2, 3, or 4.")
        return None

    return horizon


def display_current_forecast() -> None:
    """Select, build, and display a forecast."""
    horizon_days = select_forecast_horizon()

    if horizon_days is None:
        return

    try:
        forecast = build_current_financial_forecast(get_cli_user_id(), horizon_days=horizon_days)
    except ValueError as error:
        print(f"\nUnable to build forecast: {error}")
        return

    display_financial_forecast(forecast)

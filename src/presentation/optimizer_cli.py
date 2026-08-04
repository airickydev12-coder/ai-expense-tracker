from src.financial.application.financial_state import (
    build_current_financial_snapshot,
)
from src.financial.scenarios.optimizer import (
    OptimizationResult,
    optimize_financial_snapshot,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
)
from src.financial.scenarios.workspace_service import (
    save_result_to_workspace,
)
from src.presentation.cli_context import get_cli_user_id
from src.presentation.views import (
    display_optimizer_menu,
    display_optimizer_result,
)


def _read_positive_integer(
    prompt: str,
    field_name: str,
    default: int | None = None,
) -> int | None:
    """Read a positive whole-number value."""
    value_text = input(prompt).strip()

    if not value_text and default is not None:
        return default

    try:
        value = int(value_text)
    except ValueError:
        print(f"{field_name} must be a whole number.")
        return None

    if value <= 0:
        print(f"{field_name} must be greater than zero.")
        return None

    return value


def _run_optimizer(
    ranking_metric: ScenarioRankingMetric,
) -> OptimizationResult | None:
    """Run one optimizer analysis."""
    horizon_months = _read_positive_integer(
        "Optimization horizon in months " "(press Enter for 12): ",
        "Optimization horizon",
        default=12,
    )

    if horizon_months is None:
        return None

    result_limit = _read_positive_integer(
        "Number of recommendations " "(press Enter for 5): ",
        "Recommendation limit",
        default=5,
    )

    if result_limit is None:
        return None

    snapshot = build_current_financial_snapshot(get_cli_user_id())

    try:
        result = optimize_financial_snapshot(
            snapshot,
            ranking_metric=ranking_metric,
            horizon_months=horizon_months,
            limit=result_limit,
        )
    except ValueError as error:
        print(f"\nUnable to optimize financial plan: " f"{error}")
        return None

    display_optimizer_result(result)

    return result


def save_best_optimizer_result(
    result: OptimizationResult,
) -> None:
    """Offer to save the highest-ranked optimizer result."""
    best = result.best_scenario

    if best is None:
        return

    save_choice = (
        input("\nSave the best scenario to the " "planning workspace? (y/n): ")
        .strip()
        .lower()
    )

    if save_choice != "y":
        print("The optimizer result was not saved.")
        return

    save_result_to_workspace(get_cli_user_id(), best.result)

    print(f"Saved optimizer recommendation: " f"{best.scenario_name}")


def run_optimizer_flow(
    ranking_metric: ScenarioRankingMetric,
) -> None:
    """Run, display, and optionally save optimizer results."""
    result = _run_optimizer(ranking_metric)

    if result is None:
        return

    save_best_optimizer_result(result)


def manage_optimizer() -> None:
    """Run the financial optimizer menu."""
    while True:
        display_optimizer_menu()

        choice = input("Choose an option: ").strip()

        if choice == "1":
            run_optimizer_flow(ScenarioRankingMetric.OVERALL)

        elif choice == "2":
            run_optimizer_flow(ScenarioRankingMetric.NET_WORTH)

        elif choice == "3":
            run_optimizer_flow(ScenarioRankingMetric.CASH_FLOW)

        elif choice == "4":
            run_optimizer_flow(ScenarioRankingMetric.DEBT_REDUCTION)

        elif choice == "5":
            run_optimizer_flow(ScenarioRankingMetric.LOWEST_RISK)

        elif choice == "6":
            run_optimizer_flow(ScenarioRankingMetric.SUSTAINABILITY)

        elif choice == "7":
            return

        else:
            print("Invalid optimizer option. " "Please choose 1 through 7.")

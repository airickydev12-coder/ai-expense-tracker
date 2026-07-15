from src.financial.application.financial_state import (
    build_current_financial_snapshot,
)
from src.financial.scenarios.models import (
    ScenarioRequest,
    ScenarioType,
)
from src.financial.scenarios.service import (
    run_financial_scenario,
)
from src.presentation.views import (
    display_scenario_management_menu,
    display_scenario_result,
)


def _read_positive_float(
    prompt: str,
    field_name: str,
) -> float | None:
    """Read a positive floating-point value."""
    value_text = input(prompt).strip()

    try:
        value = float(value_text)
    except ValueError:
        print(f"{field_name} must be a number.")
        return None

    if value <= 0:
        print(f"{field_name} must be greater than zero.")
        return None

    return value


def _read_positive_integer(
    prompt: str,
    field_name: str,
    default: int | None = None,
) -> int | None:
    """Read a positive whole number with an optional default."""
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


def select_expense_category(
    snapshot: dict,
) -> str | None:
    """Select a category from snapshot category totals."""
    category_totals = snapshot.get(
        "category_totals",
        {},
    )

    if not category_totals:
        print("No expense-category spending is available " "for scenario modeling.")
        return None

    categories = list(category_totals)

    print("\nExpense Categories")

    for index, category in enumerate(
        categories,
        start=1,
    ):
        print(f"{index}. {category} - " f"${category_totals[category]:,.2f}")

    selection_text = input("Choose a category: ").strip()

    try:
        selection = int(selection_text)
    except ValueError:
        print("Category selection must be a number.")
        return None

    if selection < 1 or selection > len(categories):
        print("Category selection is out of range.")
        return None

    return str(categories[selection - 1])


def select_debt_id(
    snapshot: dict,
) -> int | None:
    """Select a debt from the current snapshot."""
    debts = snapshot.get(
        "debts",
        [],
    )

    if not debts:
        print("No debts are available for scenario modeling.")
        return None

    print("\nDebts")

    for index, debt in enumerate(
        debts,
        start=1,
    ):
        print(
            f"{index}. {debt['name']} | "
            f"Balance ${float(debt['balance']):,.2f} | "
            f"Rate {float(debt['interest_rate']):.2f}%"
        )

    selection_text = input("Choose a debt: ").strip()

    try:
        selection = int(selection_text)
    except ValueError:
        print("Debt selection must be a number.")
        return None

    if selection < 1 or selection > len(debts):
        print("Debt selection is out of range.")
        return None

    return int(debts[selection - 1]["id"])


def run_expense_reduction_flow(
    snapshot: dict,
) -> None:
    """Collect and run an expense-reduction scenario."""
    category = select_expense_category(snapshot)

    if category is None:
        return

    percentage = _read_positive_float(
        "Reduction percentage: ",
        "Reduction percentage",
    )

    if percentage is None:
        return

    horizon_months = _read_positive_integer(
        "Scenario horizon in months " "(press Enter for 12): ",
        "Scenario horizon",
        default=12,
    )

    if horizon_months is None:
        return

    request = ScenarioRequest(
        scenario_type=ScenarioType.EXPENSE_REDUCTION,
        name=f"{category} Expense Reduction",
        description=(f"Reduce {category} spending by " f"{percentage:g} percent."),
        parameters={
            "category": category,
            "reduction_percentage": percentage,
            "horizon_months": horizon_months,
        },
    )

    _execute_scenario(
        request,
        snapshot,
    )


def run_income_increase_flow(
    snapshot: dict,
) -> None:
    """Collect and run an income-increase scenario."""
    percentage = _read_positive_float(
        "Income increase percentage: ",
        "Income increase percentage",
    )

    if percentage is None:
        return

    horizon_months = _read_positive_integer(
        "Scenario horizon in months " "(press Enter for 12): ",
        "Scenario horizon",
        default=12,
    )

    if horizon_months is None:
        return

    request = ScenarioRequest(
        scenario_type=ScenarioType.INCOME_INCREASE,
        name="Income Increase",
        description=(f"Increase monthly income by " f"{percentage:g} percent."),
        parameters={
            "increase_percentage": percentage,
            "horizon_months": horizon_months,
        },
    )

    _execute_scenario(
        request,
        snapshot,
    )


def run_additional_savings_flow(
    snapshot: dict,
) -> None:
    """Collect and run an additional-savings scenario."""
    monthly_savings = _read_positive_float(
        "Additional monthly savings: ",
        "Additional monthly savings",
    )

    if monthly_savings is None:
        return

    horizon_months = _read_positive_integer(
        "Scenario horizon in months " "(press Enter for 12): ",
        "Scenario horizon",
        default=12,
    )

    if horizon_months is None:
        return

    request = ScenarioRequest(
        scenario_type=ScenarioType.ADDITIONAL_SAVINGS,
        name="Additional Monthly Savings",
        description=(f"Save an additional " f"${monthly_savings:,.2f} per month."),
        parameters={
            "additional_monthly_savings": monthly_savings,
            "horizon_months": horizon_months,
        },
    )

    _execute_scenario(
        request,
        snapshot,
    )


def run_extra_debt_payment_flow(
    snapshot: dict,
) -> None:
    """Collect and run an extra-debt-payment scenario."""
    debt_id = select_debt_id(snapshot)

    if debt_id is None:
        return

    extra_payment = _read_positive_float(
        "Extra monthly debt payment: ",
        "Extra monthly debt payment",
    )

    if extra_payment is None:
        return

    horizon_months = _read_positive_integer(
        "Scenario horizon in months " "(press Enter for 12): ",
        "Scenario horizon",
        default=12,
    )

    if horizon_months is None:
        return

    request = ScenarioRequest(
        scenario_type=ScenarioType.EXTRA_DEBT_PAYMENT,
        name="Extra Debt Payment",
        description=(f"Pay an additional " f"${extra_payment:,.2f} per month."),
        parameters={
            "debt_id": debt_id,
            "extra_monthly_payment": extra_payment,
            "horizon_months": horizon_months,
        },
    )

    _execute_scenario(
        request,
        snapshot,
    )


def _execute_scenario(
    request: ScenarioRequest,
    snapshot: dict,
) -> None:
    """Run and display a scenario while handling validation errors."""
    try:
        result = run_financial_scenario(
            request=request,
            snapshot=snapshot,
        )
    except ValueError as error:
        print(f"\nUnable to run scenario: {error}")
        return

    display_scenario_result(result)


def manage_scenarios() -> None:
    """Run the financial scenario-management menu."""
    while True:
        display_scenario_management_menu()

        choice = input("Choose an option: ").strip()

        if choice == "5":
            return

        snapshot = build_current_financial_snapshot()

        if choice == "1":
            run_expense_reduction_flow(snapshot)

        elif choice == "2":
            run_income_increase_flow(snapshot)

        elif choice == "3":
            run_additional_savings_flow(snapshot)

        elif choice == "4":
            run_extra_debt_payment_flow(snapshot)

        else:
            print("Invalid scenario option. " "Please choose 1 through 5.")

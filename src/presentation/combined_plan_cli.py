from src.financial.application.financial_state import (
    build_current_financial_snapshot,
)
from src.financial.scenarios.combined import (
    run_combined_scenario_plan,
)
from src.financial.scenarios.models import (
    ScenarioRequest,
    ScenarioType,
)
from src.financial.scenarios.workspace_service import (
    save_result_to_workspace,
)
from src.presentation.views import (
    display_combined_plan_builder_menu,
    display_combined_plan_result,
    display_combined_plan_steps,
)


def _read_positive_float(
    prompt: str,
    field_name: str,
) -> float | None:
    """Read a positive decimal value."""
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
    """Read a positive whole number."""
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
    """Select an expense category from the snapshot."""
    category_totals = snapshot.get(
        "category_totals",
        {},
    )

    if not category_totals:
        print("No expense-category spending is available.")
        return None

    categories = list(category_totals)

    print("\nExpense Categories")

    for index, category in enumerate(
        categories,
        start=1,
    ):
        print(f"{index}. {category} - " f"${float(category_totals[category]):,.2f}")

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
        print("No debts are available for plan modeling.")
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

    try:
        return int(debts[selection - 1]["id"])
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        print("The selected debt has an invalid ID.")
        return None


def build_expense_reduction_request(
    snapshot: dict,
) -> ScenarioRequest | None:
    """Build an expense-reduction request."""
    category = select_expense_category(snapshot)

    if category is None:
        return None

    percentage = _read_positive_float(
        "Reduction percentage: ",
        "Reduction percentage",
    )

    if percentage is None:
        return None

    if percentage > 100:
        print("Reduction percentage cannot exceed 100.")
        return None

    horizon_months = _read_positive_integer(
        "Scenario horizon in months " "(press Enter for 12): ",
        "Scenario horizon",
        default=12,
    )

    if horizon_months is None:
        return None

    return ScenarioRequest(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name=f"{category} Expense Reduction",
        description=(f"Reduce {category} spending by " f"{percentage:g} percent."),
        parameters={
            "category": category,
            "reduction_percentage": percentage,
            "horizon_months": horizon_months,
        },
    )


def build_income_increase_request() -> ScenarioRequest | None:
    """Build an income-increase request."""
    percentage = _read_positive_float(
        "Income increase percentage: ",
        "Income increase percentage",
    )

    if percentage is None:
        return None

    horizon_months = _read_positive_integer(
        "Scenario horizon in months " "(press Enter for 12): ",
        "Scenario horizon",
        default=12,
    )

    if horizon_months is None:
        return None

    return ScenarioRequest(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Income Increase",
        description=(f"Increase income by " f"{percentage:g} percent."),
        parameters={
            "increase_percentage": percentage,
            "horizon_months": horizon_months,
        },
    )


def build_additional_savings_request() -> ScenarioRequest | None:
    """Build an additional-savings request."""
    monthly_savings = _read_positive_float(
        "Additional monthly savings: ",
        "Additional monthly savings",
    )

    if monthly_savings is None:
        return None

    horizon_months = _read_positive_integer(
        "Scenario horizon in months " "(press Enter for 12): ",
        "Scenario horizon",
        default=12,
    )

    if horizon_months is None:
        return None

    return ScenarioRequest(
        scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
        name="Additional Monthly Savings",
        description=(f"Save an additional " f"${monthly_savings:,.2f} per month."),
        parameters={
            "additional_monthly_savings": (monthly_savings),
            "horizon_months": horizon_months,
        },
    )


def build_extra_debt_payment_request(
    snapshot: dict,
) -> ScenarioRequest | None:
    """Build an extra-debt-payment request."""
    debt_id = select_debt_id(snapshot)

    if debt_id is None:
        return None

    extra_payment = _read_positive_float(
        "Extra monthly debt payment: ",
        "Extra monthly debt payment",
    )

    if extra_payment is None:
        return None

    horizon_months = _read_positive_integer(
        "Scenario horizon in months " "(press Enter for 12): ",
        "Scenario horizon",
        default=12,
    )

    if horizon_months is None:
        return None

    return ScenarioRequest(
        scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
        name="Extra Debt Payment",
        description=(f"Pay an additional " f"${extra_payment:,.2f} per month."),
        parameters={
            "debt_id": debt_id,
            "extra_monthly_payment": extra_payment,
            "horizon_months": horizon_months,
        },
    )


def remove_plan_step(
    requests: list[ScenarioRequest],
) -> None:
    """Select and remove one request from the plan."""
    if not requests:
        print("No scenario steps have been added.")
        return

    display_combined_plan_steps(requests)

    selection_text = input("Choose a step to remove: ").strip()

    try:
        selection = int(selection_text)
    except ValueError:
        print("Step selection must be a number.")
        return

    if selection < 1 or selection > len(requests):
        print("Step selection is out of range.")
        return

    removed = requests.pop(selection - 1)

    print(f"Removed plan step: {removed.name}")


def run_combined_plan_builder() -> None:
    """Build and run a combined scenario plan."""
    plan_name = input("Combined plan name: ").strip()

    if not plan_name:
        print("Combined plan name cannot be empty.")
        return

    description = input("Plan description " "(optional): ").strip()

    baseline_snapshot = build_current_financial_snapshot()

    requests: list[ScenarioRequest] = []

    while True:
        display_combined_plan_builder_menu(requests)

        choice = input("Choose an option: ").strip()

        request: ScenarioRequest | None = None

        if choice == "1":
            request = build_expense_reduction_request(baseline_snapshot)

        elif choice == "2":
            request = build_income_increase_request()

        elif choice == "3":
            request = build_additional_savings_request()

        elif choice == "4":
            request = build_extra_debt_payment_request(baseline_snapshot)

        elif choice == "5":
            display_combined_plan_steps(requests)
            continue

        elif choice == "6":
            remove_plan_step(requests)
            continue

        elif choice == "7":
            if not requests:
                print("Add at least one scenario step " "before running the plan.")
                continue

            try:
                plan = run_combined_scenario_plan(
                    name=plan_name,
                    description=description,
                    requests=requests,
                    snapshot=baseline_snapshot,
                )
            except ValueError as error:
                print(f"\nUnable to run combined plan: " f"{error}")
                return

            display_combined_plan_result(plan)

            print("\nCombined plan completed successfully.")
            return

        elif choice == "8":
            print("Combined plan was cancelled.")
            return

        else:
            print("Invalid combined-plan option. " "Please choose 1 through 8.")
            continue

        if request is not None:
            requests.append(request)

            print(f"Added plan step " f"{len(requests)}: " f"{request.name}")

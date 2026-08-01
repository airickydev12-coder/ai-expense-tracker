from decimal import Decimal
from typing import Any

from src.core.exceptions import NotFoundError, ValidationError
from src.core.money import ZERO, to_money
from src.financial.scenarios.models import (
    ScenarioAssumption,
    ScenarioImpact,
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.service import (
    register_scenario_handler,
)


def _validate_percentage(
    reduction_percentage: Decimal,
) -> None:
    """Validate an expense-reduction percentage."""
    if reduction_percentage <= 0:
        raise ValidationError("Reduction percentage must be greater than zero.")

    if reduction_percentage > 100:
        raise ValidationError("Reduction percentage cannot exceed 100.")


def _validate_horizon_months(
    horizon_months: int,
) -> None:
    """Validate the scenario horizon."""
    if horizon_months <= 0:
        raise ValidationError("Scenario horizon must be greater than zero months.")


def _get_category_spending(
    snapshot: dict,
    category: str,
) -> Decimal:
    """Return spending for one category from the snapshot."""
    category_totals = snapshot.get(
        "category_totals",
        {},
    )

    normalized_category = category.strip().lower()

    for category_name, total in category_totals.items():
        if str(category_name).strip().lower() == normalized_category:
            return to_money(total)

    raise NotFoundError(f"No spending was found for category: {category}")


def run_expense_reduction_scenario(
    snapshot: dict,
    parameters: dict[str, Any],
) -> ScenarioResult:
    """Model reducing spending in one expense category."""
    category = str(
        parameters.get(
            "category",
            "",
        )
    ).strip()

    if not category:
        raise ValidationError("Expense category is required.")

    try:
        reduction_percentage = Decimal(str(parameters["reduction_percentage"]))
    except KeyError as error:
        raise ValidationError("Reduction percentage is required.") from error
    except (TypeError, ValueError, ArithmeticError) as error:
        raise ValidationError("Reduction percentage must be a number.") from error

    try:
        horizon_months = int(
            parameters.get(
                "horizon_months",
                12,
            )
        )
    except (TypeError, ValueError) as error:
        raise ValidationError("Scenario horizon must be a whole number.") from error

    _validate_percentage(reduction_percentage)
    _validate_horizon_months(horizon_months)

    category_spending = _get_category_spending(
        snapshot,
        category,
    )

    monthly_savings = category_spending * reduction_percentage / 100

    annual_savings = monthly_savings * 12
    horizon_savings = monthly_savings * horizon_months

    original_total_expenses = to_money(snapshot["total_expenses"])
    original_net_cash_flow = to_money(snapshot["net_cash_flow"])
    original_account_balance = to_money(snapshot["total_account_balance"])
    original_net_worth = to_money(snapshot["net_worth"])

    projected_total_expenses = max(
        original_total_expenses - monthly_savings,
        ZERO,
    )

    projected_net_cash_flow = original_net_cash_flow + monthly_savings

    projected_account_balance = original_account_balance + horizon_savings

    projected_net_worth = original_net_worth + horizon_savings

    projected_category_totals = dict(
        snapshot.get(
            "category_totals",
            {},
        )
    )

    matching_category_key = None

    for category_name in projected_category_totals:
        if str(category_name).strip().lower() == category.lower():
            matching_category_key = category_name
            break

    if matching_category_key is not None:
        projected_category_totals[matching_category_key] = max(
            category_spending - monthly_savings,
            ZERO,
        )

    projected_snapshot = {
        **snapshot,
        "total_expenses": projected_total_expenses,
        "net_cash_flow": projected_net_cash_flow,
        "total_account_balance": (projected_account_balance),
        "net_worth": projected_net_worth,
        "category_totals": projected_category_totals,
    }

    benefits = [
        (f"Reduce monthly {category} spending by " f"${monthly_savings:,.2f}."),
        (f"Create approximately " f"${annual_savings:,.2f} in annual savings."),
        (
            f"Increase projected net worth by "
            f"${horizon_savings:,.2f} over "
            f"{horizon_months} months."
        ),
    ]

    risks: list[str] = []

    if reduction_percentage >= 50:
        risks.append(
            "A reduction of 50 percent or more may be difficult "
            "to maintain consistently."
        )

    if category_spending <= 0:
        risks.append("The selected category currently has no measurable spending.")

    recommendations = [
        (
            f"Track {category} spending weekly to confirm "
            "the reduction target is realistic."
        ),
        (
            "Transfer the monthly savings automatically "
            "to a savings or debt-payment account."
        ),
    ]

    return ScenarioResult(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name=f"{category} Expense Reduction",
        description=(
            f"Model reducing {category} spending by "
            f"{reduction_percentage:g} percent."
        ),
        assumptions=[
            ScenarioAssumption(
                name="Expense Category",
                value=category,
                description=("The spending category being reduced."),
            ),
            ScenarioAssumption(
                name="Reduction Percentage",
                value=reduction_percentage,
                description=(
                    "The percentage reduction applied "
                    "to current monthly category spending."
                ),
            ),
            ScenarioAssumption(
                name="Scenario Horizon Months",
                value=horizon_months,
                description=(
                    "The number of months used to estimate "
                    "balance and net-worth impact."
                ),
            ),
            ScenarioAssumption(
                name="Current Category Spending",
                value=category_spending,
                description=("Current monthly spending in the " "selected category."),
            ),
        ],
        original_snapshot=snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[
            ScenarioImpact.create(
                metric="Category Spending",
                original_value=category_spending,
                projected_value=(category_spending - monthly_savings),
            ),
            ScenarioImpact.create(
                metric="Total Expenses",
                original_value=original_total_expenses,
                projected_value=projected_total_expenses,
            ),
            ScenarioImpact.create(
                metric="Net Cash Flow",
                original_value=original_net_cash_flow,
                projected_value=projected_net_cash_flow,
            ),
            ScenarioImpact.create(
                metric="Account Balance",
                original_value=original_account_balance,
                projected_value=projected_account_balance,
            ),
            ScenarioImpact.create(
                metric="Net Worth",
                original_value=original_net_worth,
                projected_value=projected_net_worth,
            ),
            ScenarioImpact.create(
                metric="Annual Savings",
                original_value=0,
                projected_value=annual_savings,
            ),
        ],
        benefits=benefits,
        risks=risks,
        recommendations=recommendations,
    )


def register_expense_reduction_scenario() -> None:
    """Register the expense-reduction scenario handler."""
    register_scenario_handler(
        ScenarioType.EXPENSE_REDUCTION,
        run_expense_reduction_scenario,
    )

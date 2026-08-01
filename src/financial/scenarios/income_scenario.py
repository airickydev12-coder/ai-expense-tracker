from decimal import Decimal
from typing import Any

from src.core.exceptions import ValidationError
from src.core.money import to_money
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
    increase_percentage: Decimal,
) -> None:
    """Validate an income-increase percentage."""
    if increase_percentage <= 0:
        raise ValidationError("Income increase percentage must be greater than zero.")

    if increase_percentage > 500:
        raise ValidationError("Income increase percentage cannot exceed 500.")


def _validate_horizon_months(
    horizon_months: int,
) -> None:
    """Validate the scenario horizon."""
    if horizon_months <= 0:
        raise ValidationError("Scenario horizon must be greater than zero months.")


def run_income_increase_scenario(
    snapshot: dict,
    parameters: dict[str, Any],
) -> ScenarioResult:
    """Model an increase in monthly income."""
    try:
        increase_percentage = Decimal(str(parameters["increase_percentage"]))
    except KeyError as error:
        raise ValidationError("Income increase percentage is required.") from error
    except (TypeError, ValueError, ArithmeticError) as error:
        raise ValidationError("Income increase percentage must be a number.") from error

    try:
        horizon_months = int(
            parameters.get(
                "horizon_months",
                12,
            )
        )
    except (TypeError, ValueError) as error:
        raise ValidationError("Scenario horizon must be a whole number.") from error

    _validate_percentage(increase_percentage)
    _validate_horizon_months(horizon_months)

    original_total_income = to_money(snapshot["total_income"])
    original_total_expenses = to_money(snapshot["total_expenses"])
    original_net_cash_flow = to_money(snapshot["net_cash_flow"])
    original_account_balance = to_money(snapshot["total_account_balance"])
    original_net_worth = to_money(snapshot["net_worth"])

    monthly_income_increase = original_total_income * increase_percentage / 100

    annual_income_increase = monthly_income_increase * 12

    horizon_income_increase = monthly_income_increase * horizon_months

    projected_total_income = original_total_income + monthly_income_increase

    projected_net_cash_flow = projected_total_income - original_total_expenses

    projected_account_balance = original_account_balance + horizon_income_increase

    projected_net_worth = original_net_worth + horizon_income_increase

    original_savings_rate = (
        original_net_cash_flow / original_total_income * 100
        if original_total_income > 0
        else Decimal("0")
    )

    projected_savings_rate = (
        projected_net_cash_flow / projected_total_income * 100
        if projected_total_income > 0
        else Decimal("0")
    )

    projected_snapshot = {
        **snapshot,
        "total_income": projected_total_income,
        "net_cash_flow": projected_net_cash_flow,
        "total_account_balance": (projected_account_balance),
        "net_worth": projected_net_worth,
    }

    benefits = [
        (f"Increase monthly income by " f"${monthly_income_increase:,.2f}."),
        (f"Increase annual income by " f"${annual_income_increase:,.2f}."),
        (
            f"Increase projected net worth by "
            f"${horizon_income_increase:,.2f} over "
            f"{horizon_months} months."
        ),
    ]

    risks: list[str] = []

    if increase_percentage >= 50:
        risks.append(
            "A projected income increase of 50 percent or more "
            "may require a major career or business change."
        )

    if original_total_income <= 0:
        risks.append("The current snapshot has no positive income baseline.")

    recommendations = [
        (
            "Direct part of the additional income toward "
            "high-priority debt or savings goals."
        ),
        ("Avoid increasing recurring expenses until the " "higher income is stable."),
    ]

    return ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Income Increase",
        description=(
            "Model increasing monthly income by " f"{increase_percentage:g} percent."
        ),
        assumptions=[
            ScenarioAssumption(
                name="Income Increase Percentage",
                value=increase_percentage,
                description=("The percentage applied to current " "monthly income."),
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
                name="Current Monthly Income",
                value=original_total_income,
                description=("The current monthly income baseline."),
            ),
        ],
        original_snapshot=snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[
            ScenarioImpact.create(
                metric="Total Income",
                original_value=original_total_income,
                projected_value=projected_total_income,
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
                metric="Annual Income Increase",
                original_value=0,
                projected_value=annual_income_increase,
            ),
            ScenarioImpact.create(
                metric="Savings Rate",
                original_value=original_savings_rate,
                projected_value=projected_savings_rate,
            ),
        ],
        benefits=benefits,
        risks=risks,
        recommendations=recommendations,
    )


def register_income_increase_scenario() -> None:
    """Register the income-increase scenario handler."""
    register_scenario_handler(
        ScenarioType.INCOME_INCREASE,
        run_income_increase_scenario,
    )

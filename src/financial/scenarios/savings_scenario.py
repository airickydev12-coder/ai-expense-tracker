from decimal import Decimal
from typing import Any

from src.core.constants import MONTHS_PER_YEAR
from src.core.exceptions import ValidationError
from src.core.money import to_money
from src.financial.scenarios.comparison import (
    METRIC_ACCOUNT_BALANCE,
    METRIC_GOAL_PROGRESS,
    METRIC_NET_WORTH,
)
from src.financial.scenarios.models import (
    ScenarioAssumption,
    ScenarioImpact,
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.service import (
    register_scenario_handler,
)


def _validate_monthly_savings(
    additional_monthly_savings: Decimal,
) -> None:
    """Validate the additional monthly savings amount."""
    if additional_monthly_savings <= 0:
        raise ValidationError("Additional monthly savings must be greater than zero.")


def _validate_horizon_months(
    horizon_months: int,
) -> None:
    """Validate the scenario horizon."""
    if horizon_months <= 0:
        raise ValidationError("Scenario horizon must be greater than zero months.")


def run_additional_savings_scenario(
    snapshot: dict,
    parameters: dict[str, Any],
) -> ScenarioResult:
    """Model saving an additional amount each month."""
    try:
        additional_monthly_savings = to_money(parameters["additional_monthly_savings"])
    except KeyError as error:
        raise ValidationError("Additional monthly savings is required.") from error
    except (TypeError, ValueError) as error:
        raise ValidationError("Additional monthly savings must be a number.") from error

    try:
        horizon_months = int(
            parameters.get(
                "horizon_months",
                12,
            )
        )
    except (TypeError, ValueError) as error:
        raise ValidationError("Scenario horizon must be a whole number.") from error

    _validate_monthly_savings(additional_monthly_savings)
    _validate_horizon_months(horizon_months)

    original_total_income = to_money(snapshot["total_income"])
    original_net_cash_flow = to_money(snapshot["net_cash_flow"])
    original_account_balance = to_money(snapshot["total_account_balance"])
    original_goal_progress = to_money(snapshot["total_goal_progress"])
    original_net_worth = to_money(snapshot["net_worth"])

    annual_additional_savings = additional_monthly_savings * MONTHS_PER_YEAR

    horizon_additional_savings = additional_monthly_savings * horizon_months

    projected_net_cash_flow = original_net_cash_flow - additional_monthly_savings

    projected_account_balance = original_account_balance + horizon_additional_savings

    projected_goal_progress = original_goal_progress + horizon_additional_savings

    projected_net_worth = original_net_worth + horizon_additional_savings

    original_savings_rate = (
        original_net_cash_flow / original_total_income * 100
        if original_total_income > 0
        else Decimal("0")
    )

    projected_savings_rate = (
        (original_net_cash_flow + additional_monthly_savings)
        / original_total_income
        * 100
        if original_total_income > 0
        else Decimal("0")
    )

    projected_snapshot = {
        **snapshot,
        "net_cash_flow": projected_net_cash_flow,
        "total_account_balance": (projected_account_balance),
        "total_goal_progress": (projected_goal_progress),
        "net_worth": projected_net_worth,
    }

    benefits = [
        (f"Add ${additional_monthly_savings:,.2f} " "to savings each month."),
        (
            f"Create approximately "
            f"${annual_additional_savings:,.2f} "
            "in additional annual savings."
        ),
        (
            f"Increase projected net worth by "
            f"${horizon_additional_savings:,.2f} over "
            f"{horizon_months} months."
        ),
    ]

    risks: list[str] = []

    if additional_monthly_savings > original_net_cash_flow:
        risks.append(
            "The additional savings amount exceeds current " "monthly net cash flow."
        )

    if projected_net_cash_flow < 0:
        risks.append(
            "This savings target would create negative " "monthly available cash flow."
        )

    recommendations = [
        (
            "Automate the additional savings transfer "
            "immediately after income is received."
        ),
        ("Keep enough accessible cash for bills and " "unexpected expenses."),
    ]

    return ScenarioResult(
        scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
        name="Additional Monthly Savings",
        description=(
            "Model saving an additional "
            f"${additional_monthly_savings:,.2f} per month."
        ),
        assumptions=[
            ScenarioAssumption(
                name="Additional Monthly Savings",
                value=additional_monthly_savings,
                description=("The extra amount transferred to " "savings each month."),
            ),
            ScenarioAssumption(
                name="Scenario Horizon Months",
                value=horizon_months,
                description=(
                    "The number of months used to estimate "
                    "savings and net-worth impact."
                ),
            ),
            ScenarioAssumption(
                name="Current Net Cash Flow",
                value=original_net_cash_flow,
                description=("The current monthly cash-flow baseline."),
            ),
        ],
        original_snapshot=snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[
            ScenarioImpact.create(
                metric="Monthly Available Cash Flow",
                original_value=original_net_cash_flow,
                projected_value=projected_net_cash_flow,
            ),
            ScenarioImpact.create(
                metric=METRIC_ACCOUNT_BALANCE,
                original_value=original_account_balance,
                projected_value=projected_account_balance,
            ),
            ScenarioImpact.create(
                metric=METRIC_GOAL_PROGRESS,
                original_value=original_goal_progress,
                projected_value=projected_goal_progress,
            ),
            ScenarioImpact.create(
                metric=METRIC_NET_WORTH,
                original_value=original_net_worth,
                projected_value=projected_net_worth,
            ),
            ScenarioImpact.create(
                metric="Annual Additional Savings",
                original_value=0,
                projected_value=annual_additional_savings,
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


def register_additional_savings_scenario() -> None:
    """Register the additional-savings scenario handler."""
    register_scenario_handler(
        ScenarioType.ADDITIONAL_SAVINGS,
        run_additional_savings_scenario,
    )

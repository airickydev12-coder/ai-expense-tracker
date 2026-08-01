from dataclasses import dataclass
from decimal import Decimal
from typing import Any

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


MAX_PAYOFF_MONTHS = 1200
BALANCE_TOLERANCE = Decimal("0.005")


@dataclass(frozen=True)
class DebtPayoffProjection:
    """Represents the result of a debt payoff calculation."""

    payoff_months: int
    total_interest: Decimal
    remaining_balance_at_horizon: Decimal
    interest_paid_at_horizon: Decimal


def _validate_extra_payment(
    extra_monthly_payment: Decimal,
) -> None:
    """Validate the additional monthly debt payment."""
    if extra_monthly_payment <= 0:
        raise ValueError("Extra monthly debt payment must be greater than zero.")


def _validate_horizon_months(
    horizon_months: int,
) -> None:
    """Validate the scenario horizon."""
    if horizon_months <= 0:
        raise ValueError("Scenario horizon must be greater than zero months.")


def _get_debt(
    snapshot: dict,
    debt_id: int,
) -> dict:
    """Return a debt from the serialized snapshot."""
    debts = snapshot.get("debts", [])

    for debt in debts:
        try:
            current_debt_id = int(debt["id"])
        except (KeyError, TypeError, ValueError):
            continue

        if current_debt_id == debt_id:
            return debt.copy()

    raise ValueError(f"No debt was found with ID: {debt_id}")


def _validate_debt_values(
    balance: Decimal,
    interest_rate: Decimal,
    minimum_payment: Decimal,
) -> None:
    """Validate values required for debt amortization."""
    if balance <= 0:
        raise ValueError("Debt balance must be greater than zero.")

    if interest_rate < 0:
        raise ValueError("Debt interest rate cannot be negative.")

    if minimum_payment <= 0:
        raise ValueError("Debt minimum payment must be greater than zero.")

    monthly_interest = balance * interest_rate / 100 / 12

    if minimum_payment <= monthly_interest:
        raise ValueError(
            "Debt minimum payment must exceed the " "first month's interest charge."
        )


def calculate_debt_payoff(
    *,
    balance: Decimal | float | int,
    annual_interest_rate: Decimal | float | int,
    monthly_payment: Decimal | float | int,
    horizon_months: int,
) -> DebtPayoffProjection:
    """Calculate debt payoff and horizon statistics."""
    balance = to_money(balance)
    annual_interest_rate = Decimal(str(annual_interest_rate))
    monthly_payment = to_money(monthly_payment)

    if balance <= 0:
        raise ValueError("Debt balance must be greater than zero.")

    if annual_interest_rate < 0:
        raise ValueError("Debt interest rate cannot be negative.")

    if monthly_payment <= 0:
        raise ValueError("Monthly payment must be greater than zero.")

    _validate_horizon_months(horizon_months)

    monthly_rate = annual_interest_rate / 100 / 12

    first_month_interest = balance * monthly_rate

    if monthly_payment <= first_month_interest:
        raise ValueError("Monthly payment is not sufficient " "to amortize the debt.")

    remaining_balance = to_money(balance)
    total_interest = ZERO
    interest_paid_at_horizon = ZERO
    remaining_balance_at_horizon = remaining_balance
    payoff_months = 0

    while remaining_balance > BALANCE_TOLERANCE and payoff_months < MAX_PAYOFF_MONTHS:
        monthly_interest = remaining_balance * monthly_rate

        payment = min(
            monthly_payment,
            remaining_balance + monthly_interest,
        )

        principal_payment = payment - monthly_interest

        remaining_balance = max(
            remaining_balance - principal_payment,
            ZERO,
        )

        total_interest += monthly_interest
        payoff_months += 1

        if payoff_months <= horizon_months:
            interest_paid_at_horizon += monthly_interest
            remaining_balance_at_horizon = remaining_balance

    if remaining_balance > BALANCE_TOLERANCE:
        raise ValueError(
            "Debt could not be paid off within " f"{MAX_PAYOFF_MONTHS} months."
        )

    if payoff_months < horizon_months:
        remaining_balance_at_horizon = ZERO

    return DebtPayoffProjection(
        payoff_months=payoff_months,
        total_interest=total_interest,
        remaining_balance_at_horizon=(remaining_balance_at_horizon),
        interest_paid_at_horizon=(interest_paid_at_horizon),
    )


def run_extra_debt_payment_scenario(
    snapshot: dict,
    parameters: dict[str, Any],
) -> ScenarioResult:
    """Model making an additional monthly debt payment."""
    try:
        debt_id = int(parameters["debt_id"])
    except KeyError as error:
        raise ValueError("Debt ID is required.") from error
    except (TypeError, ValueError) as error:
        raise ValueError("Debt ID must be a whole number.") from error

    try:
        extra_monthly_payment = to_money(parameters["extra_monthly_payment"])
    except KeyError as error:
        raise ValueError("Extra monthly debt payment is required.") from error
    except (TypeError, ValueError) as error:
        raise ValueError("Extra monthly debt payment must be a number.") from error

    try:
        horizon_months = int(
            parameters.get(
                "horizon_months",
                12,
            )
        )
    except (TypeError, ValueError) as error:
        raise ValueError("Scenario horizon must be a whole number.") from error

    _validate_extra_payment(extra_monthly_payment)
    _validate_horizon_months(horizon_months)

    debt = _get_debt(
        snapshot,
        debt_id,
    )

    debt_name = str(
        debt.get(
            "name",
            f"Debt {debt_id}",
        )
    ).strip()

    balance = to_money(debt["balance"])
    interest_rate = Decimal(str(debt["interest_rate"]))
    minimum_payment = to_money(debt["minimum_payment"])

    _validate_debt_values(
        balance,
        interest_rate,
        minimum_payment,
    )

    accelerated_payment = minimum_payment + extra_monthly_payment

    baseline_projection = calculate_debt_payoff(
        balance=balance,
        annual_interest_rate=interest_rate,
        monthly_payment=minimum_payment,
        horizon_months=horizon_months,
    )

    accelerated_projection = calculate_debt_payoff(
        balance=balance,
        annual_interest_rate=interest_rate,
        monthly_payment=accelerated_payment,
        horizon_months=horizon_months,
    )

    payoff_months_saved = max(
        baseline_projection.payoff_months - accelerated_projection.payoff_months,
        0,
    )

    total_interest_saved = max(
        baseline_projection.total_interest - accelerated_projection.total_interest,
        ZERO,
    )

    horizon_interest_saved = max(
        baseline_projection.interest_paid_at_horizon
        - accelerated_projection.interest_paid_at_horizon,
        ZERO,
    )

    additional_debt_reduction = max(
        baseline_projection.remaining_balance_at_horizon
        - accelerated_projection.remaining_balance_at_horizon,
        ZERO,
    )

    original_total_debt = to_money(snapshot["total_debt"])
    original_net_cash_flow = to_money(snapshot["net_cash_flow"])
    original_net_worth = to_money(snapshot["net_worth"])

    projected_total_debt = max(
        original_total_debt
        - balance
        + accelerated_projection.remaining_balance_at_horizon,
        ZERO,
    )

    projected_net_cash_flow = original_net_cash_flow - extra_monthly_payment

    projected_net_worth = original_net_worth + horizon_interest_saved

    projected_debts: list[dict] = []

    for current_debt in snapshot.get(
        "debts",
        [],
    ):
        projected_debt = current_debt.copy()

        try:
            current_debt_id = int(projected_debt["id"])
        except (KeyError, TypeError, ValueError):
            projected_debts.append(projected_debt)
            continue

        if current_debt_id == debt_id:
            projected_debt["balance"] = (
                accelerated_projection.remaining_balance_at_horizon
            )

        projected_debts.append(projected_debt)

    projected_snapshot = {
        **snapshot,
        "total_debt": projected_total_debt,
        "net_cash_flow": projected_net_cash_flow,
        "net_worth": projected_net_worth,
        "debts": projected_debts,
    }

    benefits = [
        (f"Pay off {debt_name} approximately " f"{payoff_months_saved} months sooner."),
        (
            f"Save approximately "
            f"${total_interest_saved:,.2f} "
            "in lifetime interest."
        ),
        (
            f"Reduce the selected debt balance by an "
            f"additional ${additional_debt_reduction:,.2f} "
            f"over {horizon_months} months."
        ),
    ]

    risks: list[str] = []

    if extra_monthly_payment > original_net_cash_flow:
        risks.append("The extra payment exceeds current " "monthly net cash flow.")

    if projected_net_cash_flow < 0:
        risks.append(
            "This payment plan would create negative " "monthly available cash flow."
        )

    if interest_rate < 5:
        risks.append(
            "This debt has a relatively low interest rate; "
            "confirm that extra payments are preferable to "
            "other savings or investment priorities."
        )

    recommendations = [
        ("Confirm that the lender applies extra payments " "directly to principal."),
        (
            "Maintain an emergency cash reserve before "
            "committing all available cash flow to debt."
        ),
    ]

    return ScenarioResult(
        scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
        name=f"Extra Payment on {debt_name}",
        description=(
            f"Model paying an additional "
            f"${extra_monthly_payment:,.2f} per month "
            f"toward {debt_name}."
        ),
        assumptions=[
            ScenarioAssumption(
                name="Debt ID",
                value=debt_id,
                description=("The identifier of the selected debt."),
            ),
            ScenarioAssumption(
                name="Debt Name",
                value=debt_name,
                description=("The debt receiving the extra payment."),
            ),
            ScenarioAssumption(
                name="Extra Monthly Payment",
                value=extra_monthly_payment,
                description=(
                    "The amount paid in addition to the " "current minimum payment."
                ),
            ),
            ScenarioAssumption(
                name="Current Minimum Payment",
                value=minimum_payment,
                description=("The existing required monthly payment."),
            ),
            ScenarioAssumption(
                name="Interest Rate",
                value=interest_rate,
                description=("The debt's annual interest rate."),
            ),
            ScenarioAssumption(
                name="Scenario Horizon Months",
                value=horizon_months,
                description=(
                    "The number of months used for the " "projected snapshot."
                ),
            ),
        ],
        original_snapshot=snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[
            ScenarioImpact.create(
                metric="Selected Debt Balance",
                original_value=balance,
                projected_value=(accelerated_projection.remaining_balance_at_horizon),
            ),
            ScenarioImpact.create(
                metric="Total Debt",
                original_value=original_total_debt,
                projected_value=projected_total_debt,
            ),
            ScenarioImpact.create(
                metric="Monthly Available Cash Flow",
                original_value=original_net_cash_flow,
                projected_value=projected_net_cash_flow,
            ),
            ScenarioImpact.create(
                metric="Net Worth",
                original_value=original_net_worth,
                projected_value=projected_net_worth,
            ),
            ScenarioImpact.create(
                metric="Payoff Months",
                original_value=(baseline_projection.payoff_months),
                projected_value=(accelerated_projection.payoff_months),
            ),
            ScenarioImpact.create(
                metric="Lifetime Interest",
                original_value=(baseline_projection.total_interest),
                projected_value=(accelerated_projection.total_interest),
            ),
            ScenarioImpact.create(
                metric="Lifetime Interest Savings",
                original_value=0,
                projected_value=total_interest_saved,
            ),
        ],
        benefits=benefits,
        risks=risks,
        recommendations=recommendations,
    )


def register_extra_debt_payment_scenario() -> None:
    """Register the extra-debt-payment handler."""
    register_scenario_handler(
        ScenarioType.EXTRA_DEBT_PAYMENT,
        run_extra_debt_payment_scenario,
    )

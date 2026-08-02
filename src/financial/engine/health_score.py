from dataclasses import dataclass


@dataclass(frozen=True)
class HealthScoreFactor:
    """One contributing factor behind a calculated health score."""

    name: str
    points: int
    description: str


def explain_health_score(snapshot: dict) -> list[HealthScoreFactor]:
    """
    Return the per-factor point breakdown behind calculate_health_score's total.

    Score range:
        0 to 100
    """
    factors = [
        HealthScoreFactor(
            name="Baseline",
            points=50,
            description="Starting baseline score.",
        )
    ]

    if snapshot["net_cash_flow"] > 0:
        factors.append(
            HealthScoreFactor(
                name="Cash Flow",
                points=20,
                description="Monthly income exceeds monthly expenses.",
            )
        )
    elif snapshot["net_cash_flow"] < 0:
        factors.append(
            HealthScoreFactor(
                name="Cash Flow",
                points=-20,
                description="Monthly expenses exceed monthly income.",
            )
        )
    else:
        factors.append(
            HealthScoreFactor(
                name="Cash Flow",
                points=0,
                description="Monthly income and expenses are balanced.",
            )
        )

    if snapshot["total_debt"] == 0:
        factors.append(
            HealthScoreFactor(
                name="Debt Load",
                points=15,
                description="No outstanding debt.",
            )
        )
    elif snapshot["total_debt"] > snapshot["total_account_balance"]:
        factors.append(
            HealthScoreFactor(
                name="Debt Load",
                points=-15,
                description="Total debt exceeds total account balance.",
            )
        )
    else:
        factors.append(
            HealthScoreFactor(
                name="Debt Load",
                points=0,
                description="Debt is present but does not exceed account balance.",
            )
        )

    if snapshot["total_goal_progress"] > 0:
        factors.append(
            HealthScoreFactor(
                name="Goal Progress",
                points=10,
                description="Progress has been made toward at least one goal.",
            )
        )
    else:
        factors.append(
            HealthScoreFactor(
                name="Goal Progress",
                points=0,
                description="No progress recorded toward any goal.",
            )
        )

    if snapshot["net_worth"] > 0:
        factors.append(
            HealthScoreFactor(
                name="Net Worth",
                points=5,
                description="Net worth is positive.",
            )
        )
    elif snapshot["net_worth"] < 0:
        factors.append(
            HealthScoreFactor(
                name="Net Worth",
                points=-10,
                description="Net worth is negative.",
            )
        )
    else:
        factors.append(
            HealthScoreFactor(
                name="Net Worth",
                points=0,
                description="Net worth is exactly zero.",
            )
        )

    return factors


def calculate_health_score(snapshot: dict) -> int:
    """
    Calculate a basic financial health score from a financial snapshot.

    Score range:
        0 to 100
    """
    total = sum(factor.points for factor in explain_health_score(snapshot))

    return max(0, min(100, total))

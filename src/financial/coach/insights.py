from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.core.constants import MONTHS_PER_YEAR
from src.core.exceptions import ValidationError
from src.core.money import ZERO, to_money
from src.financial.coach.models import CoachingCategory
from src.financial.scenarios.comparison import (
    METRIC_NET_CASH_FLOW,
    METRIC_NET_WORTH,
    METRIC_TOTAL_DEBT,
)

SAVINGS_RATE_LOW_THRESHOLD = 10
SAVINGS_RATE_STRONG_THRESHOLD = 20

EMERGENCY_FUND_MINIMAL_MONTHS_THRESHOLD = 1
EMERGENCY_FUND_TARGET_MONTHS_THRESHOLD = 3
EMERGENCY_FUND_STRONG_MONTHS_THRESHOLD = 6

DEBT_TO_INCOME_CRITICAL_THRESHOLD = 50
DEBT_TO_INCOME_ELEVATED_THRESHOLD = 30

SPENDING_CONCENTRATION_WARNING_THRESHOLD = 50

HEALTH_SCORE_CRITICAL_THRESHOLD = 40
HEALTH_SCORE_WARNING_THRESHOLD = 60
HEALTH_SCORE_INFORMATIONAL_THRESHOLD = 80


class InsightSeverity(Enum):
    """Severity assigned to a financial coaching insight."""

    POSITIVE = "Positive"
    INFORMATIONAL = "Informational"
    WARNING = "Warning"
    CRITICAL = "Critical"


@dataclass(frozen=True)
class FinancialCoachInsight:
    """Represents one deterministic financial coaching insight."""

    key: str
    title: str
    message: str
    category: CoachingCategory
    severity: InsightSeverity
    metric: str = ""
    current_value: float | None = None
    benchmark_value: float | None = None
    action: str = ""

    def __post_init__(self) -> None:
        """Validate and normalize insight data."""
        normalized_key = self.key.strip()
        normalized_title = self.title.strip()
        normalized_message = self.message.strip()

        if not normalized_key:
            raise ValidationError("Financial insight key cannot be empty.")

        if not normalized_title:
            raise ValidationError("Financial insight title cannot be empty.")

        if not normalized_message:
            raise ValidationError("Financial insight message cannot be empty.")

        object.__setattr__(
            self,
            "key",
            normalized_key,
        )
        object.__setattr__(
            self,
            "title",
            normalized_title,
        )
        object.__setattr__(
            self,
            "message",
            normalized_message,
        )
        object.__setattr__(
            self,
            "metric",
            self.metric.strip(),
        )
        object.__setattr__(
            self,
            "action",
            self.action.strip(),
        )

    def to_dict(self) -> dict:
        """Convert the insight to a dictionary."""
        return {
            "key": self.key,
            "title": self.title,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "metric": self.metric,
            "current_value": self.current_value,
            "benchmark_value": self.benchmark_value,
            "action": self.action,
        }


def _to_money(
    value: object,
    default: Decimal = ZERO,
) -> Decimal:
    """Convert a supported value to Decimal safely."""
    if value is None:
        return default

    try:
        return to_money(value)
    except TypeError, ValueError:
        return default


def _to_float(
    value: int | float | str | None,
    default: float = 0.0,
) -> float:
    """Convert a supported value to float safely."""
    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def calculate_savings_rate(
    snapshot: dict,
) -> float | None:
    """Calculate net cash flow as a percentage of income."""
    total_income = _to_money(
        snapshot.get(
            "total_income",
            ZERO,
        )
    )

    if total_income <= 0:
        return None

    net_cash_flow = _to_money(
        snapshot.get(
            "net_cash_flow",
            ZERO,
        )
    )

    return float(net_cash_flow / total_income * 100)


def calculate_debt_to_income_ratio(
    snapshot: dict,
) -> float | None:
    """
    Calculate total debt relative to annualized income.

    Monthly income is multiplied by 12 before comparison.
    """
    monthly_income = _to_money(
        snapshot.get(
            "total_income",
            ZERO,
        )
    )

    if monthly_income <= 0:
        return None

    total_debt = _to_money(
        snapshot.get(
            "total_debt",
            ZERO,
        )
    )

    annual_income = monthly_income * MONTHS_PER_YEAR

    return float(total_debt / annual_income * 100)


def calculate_emergency_fund_months(
    snapshot: dict,
) -> float | None:
    """Estimate how many months of expenses account balances cover."""
    monthly_expenses = _to_money(
        snapshot.get(
            "total_expenses",
            ZERO,
        )
    )

    if monthly_expenses <= 0:
        return None

    account_balance = _to_money(
        snapshot.get(
            "total_account_balance",
            ZERO,
        )
    )

    return float(account_balance / monthly_expenses)


def find_top_spending_category(
    snapshot: dict,
) -> tuple[str, Decimal] | None:
    """Return the category with the highest spending total."""
    category_totals = snapshot.get(
        "category_totals",
        {},
    )

    if not isinstance(
        category_totals,
        dict,
    ):
        return None

    valid_totals: list[tuple[str, Decimal]] = []

    for category, value in category_totals.items():
        category_name = str(category).strip()
        amount = _to_money(value)

        if not category_name or amount <= 0:
            continue

        valid_totals.append(
            (
                category_name,
                amount,
            )
        )

    if not valid_totals:
        return None

    return max(
        valid_totals,
        key=lambda item: (
            item[1],
            item[0].lower(),
        ),
    )


def build_cash_flow_insights(
    snapshot: dict,
) -> list[FinancialCoachInsight]:
    """Build insights related to monthly cash flow."""
    net_cash_flow = _to_money(
        snapshot.get(
            "net_cash_flow",
            ZERO,
        )
    )

    if net_cash_flow < 0:
        return [
            FinancialCoachInsight(
                key="cash_flow:negative",
                title="Negative Monthly Cash Flow",
                message=("Monthly expenses currently exceed " "monthly income."),
                category=CoachingCategory.CASH_FLOW,
                severity=InsightSeverity.CRITICAL,
                metric=METRIC_NET_CASH_FLOW,
                current_value=float(net_cash_flow),
                benchmark_value=0.0,
                action=(
                    "Reduce expenses or increase income "
                    "until monthly cash flow is positive."
                ),
            )
        ]

    if net_cash_flow == 0:
        return [
            FinancialCoachInsight(
                key="cash_flow:break_even",
                title="No Monthly Cash Flow Margin",
                message=(
                    "Income currently covers expenses, but "
                    "there is no remaining monthly margin."
                ),
                category=CoachingCategory.CASH_FLOW,
                severity=InsightSeverity.WARNING,
                metric=METRIC_NET_CASH_FLOW,
                current_value=float(net_cash_flow),
                benchmark_value=1.0,
                action=(
                    "Create a small monthly surplus before "
                    "adding new financial commitments."
                ),
            )
        ]

    return [
        FinancialCoachInsight(
            key="cash_flow:positive",
            title="Positive Monthly Cash Flow",
            message=(f"The current monthly surplus is " f"${net_cash_flow:,.2f}."),
            category=CoachingCategory.CASH_FLOW,
            severity=InsightSeverity.POSITIVE,
            metric=METRIC_NET_CASH_FLOW,
            current_value=float(net_cash_flow),
            benchmark_value=0.0,
            action=(
                "Assign the surplus deliberately across "
                "savings, debt reduction, and goals."
            ),
        )
    ]


def build_savings_rate_insights(
    snapshot: dict,
) -> list[FinancialCoachInsight]:
    """Build insights related to the estimated savings rate."""
    savings_rate = calculate_savings_rate(snapshot)

    if savings_rate is None:
        return []

    if savings_rate < 0:
        severity = InsightSeverity.CRITICAL
        title = "Negative Savings Rate"
        message = (
            "The current financial position is consuming "
            "more income than it generates."
        )
        action = (
            "Restore positive monthly cash flow before "
            "increasing savings commitments."
        )

    elif savings_rate < SAVINGS_RATE_LOW_THRESHOLD:
        severity = InsightSeverity.WARNING
        title = "Low Savings Capacity"
        message = f"The estimated savings rate is " f"{savings_rate:.1f}%."
        action = "Work toward saving at least 10% of monthly income."

    elif savings_rate < SAVINGS_RATE_STRONG_THRESHOLD:
        severity = InsightSeverity.INFORMATIONAL
        title = "Moderate Savings Capacity"
        message = f"The estimated savings rate is " f"{savings_rate:.1f}%."
        action = (
            "Consider gradually increasing the savings rate "
            "toward 20% when practical."
        )

    else:
        severity = InsightSeverity.POSITIVE
        title = "Strong Savings Capacity"
        message = f"The estimated savings rate is " f"{savings_rate:.1f}%."
        action = (
            "Maintain the surplus while balancing savings, "
            "debt reduction, and long-term goals."
        )

    return [
        FinancialCoachInsight(
            key="savings:rate",
            title=title,
            message=message,
            category=CoachingCategory.SAVINGS,
            severity=severity,
            metric="Savings Rate",
            current_value=savings_rate,
            benchmark_value=float(SAVINGS_RATE_STRONG_THRESHOLD),
            action=action,
        )
    ]


def build_emergency_fund_insights(
    snapshot: dict,
) -> list[FinancialCoachInsight]:
    """Build insights related to emergency-fund coverage."""
    coverage_months = calculate_emergency_fund_months(snapshot)

    if coverage_months is None:
        return []

    if coverage_months < EMERGENCY_FUND_MINIMAL_MONTHS_THRESHOLD:
        severity = InsightSeverity.CRITICAL
        title = "Minimal Emergency Coverage"
        action = "Prioritize building at least one month of " "essential expenses."

    elif coverage_months < EMERGENCY_FUND_TARGET_MONTHS_THRESHOLD:
        severity = InsightSeverity.WARNING
        title = "Emergency Fund Below Target"
        action = (
            "Continue building reserves toward at least " "three months of expenses."
        )

    elif coverage_months < EMERGENCY_FUND_STRONG_MONTHS_THRESHOLD:
        severity = InsightSeverity.INFORMATIONAL
        title = "Emergency Fund Is Developing"
        action = (
            "Consider extending coverage toward six months " "for greater resilience."
        )

    else:
        severity = InsightSeverity.POSITIVE
        title = "Strong Emergency Coverage"
        action = (
            "Maintain the reserve and review the target "
            "after major life or expense changes."
        )

    return [
        FinancialCoachInsight(
            key="savings:emergency_fund",
            title=title,
            message=(
                "Available account balances cover "
                f"approximately {coverage_months:.1f} "
                "months of current expenses."
            ),
            category=CoachingCategory.SAVINGS,
            severity=severity,
            metric="Emergency Fund Months",
            current_value=coverage_months,
            benchmark_value=float(EMERGENCY_FUND_STRONG_MONTHS_THRESHOLD),
            action=action,
        )
    ]


def build_debt_insights(
    snapshot: dict,
) -> list[FinancialCoachInsight]:
    """Build insights related to debt burden."""
    total_debt = _to_money(
        snapshot.get(
            "total_debt",
            ZERO,
        )
    )

    if total_debt <= 0:
        return [
            FinancialCoachInsight(
                key="debt:none",
                title="No Debt Recorded",
                message=(
                    "No outstanding debt is included in the "
                    "current financial snapshot."
                ),
                category=CoachingCategory.DEBT,
                severity=InsightSeverity.POSITIVE,
                metric=METRIC_TOTAL_DEBT,
                current_value=0.0,
                benchmark_value=0.0,
                action=(
                    "Direct available cash flow toward "
                    "savings and long-term financial goals."
                ),
            )
        ]

    debt_ratio = calculate_debt_to_income_ratio(snapshot)

    insights = [
        FinancialCoachInsight(
            key="debt:balance",
            title="Outstanding Debt Requires a Plan",
            message=(f"Total recorded debt is " f"${total_debt:,.2f}."),
            category=CoachingCategory.DEBT,
            severity=InsightSeverity.INFORMATIONAL,
            metric=METRIC_TOTAL_DEBT,
            current_value=float(total_debt),
            benchmark_value=0.0,
            action=(
                "Prioritize high-interest balances while "
                "maintaining minimum payments on all debts."
            ),
        )
    ]

    if debt_ratio is None:
        return insights

    if debt_ratio > DEBT_TO_INCOME_CRITICAL_THRESHOLD:
        severity = InsightSeverity.CRITICAL
        title = "High Debt-to-Income Burden"
        action = (
            "Avoid new debt and prioritize aggressive " "repayment of costly balances."
        )

    elif debt_ratio > DEBT_TO_INCOME_ELEVATED_THRESHOLD:
        severity = InsightSeverity.WARNING
        title = "Elevated Debt-to-Income Burden"
        action = (
            "Use a structured debt-reduction plan and " "limit additional borrowing."
        )

    else:
        severity = InsightSeverity.INFORMATIONAL
        title = "Manageable Debt-to-Income Level"
        action = (
            "Continue scheduled repayment and target " "high-interest balances first."
        )

    insights.append(
        FinancialCoachInsight(
            key="debt:income_ratio",
            title=title,
            message=(
                "Total debt equals approximately "
                f"{debt_ratio:.1f}% of annualized income."
            ),
            category=CoachingCategory.DEBT,
            severity=severity,
            metric="Debt-to-Income Ratio",
            current_value=debt_ratio,
            benchmark_value=float(DEBT_TO_INCOME_ELEVATED_THRESHOLD),
            action=action,
        )
    )

    return insights


def build_spending_insights(
    snapshot: dict,
) -> list[FinancialCoachInsight]:
    """Build insights related to spending concentration."""
    top_category = find_top_spending_category(snapshot)

    if top_category is None:
        return []

    category, amount = top_category

    total_expenses = _to_money(
        snapshot.get(
            "total_expenses",
            ZERO,
        )
    )

    concentration = float(amount / total_expenses * 100) if total_expenses > 0 else 0.0

    severity = (
        InsightSeverity.WARNING
        if concentration >= SPENDING_CONCENTRATION_WARNING_THRESHOLD
        else InsightSeverity.INFORMATIONAL
    )

    return [
        FinancialCoachInsight(
            key=("spending:top_category:" f"{category.lower().replace(' ', '_')}"),
            title=f"{category} Is the Largest Spending Category",
            message=(
                f"{category} spending is "
                f"${amount:,.2f}, representing approximately "
                f"{concentration:.1f}% of total expenses."
            ),
            category=CoachingCategory.SPENDING,
            severity=severity,
            metric="Spending Concentration",
            current_value=concentration,
            benchmark_value=float(SPENDING_CONCENTRATION_WARNING_THRESHOLD),
            action=(
                f"Review {category} spending for realistic "
                "opportunities to reduce or optimize costs."
            ),
        )
    ]


def build_net_worth_insights(
    snapshot: dict,
) -> list[FinancialCoachInsight]:
    """Build insights related to current net worth."""
    net_worth = _to_money(
        snapshot.get(
            "net_worth",
            ZERO,
        )
    )

    if net_worth < 0:
        return [
            FinancialCoachInsight(
                key="net_worth:negative",
                title="Negative Net Worth",
                message=(
                    f"Current liabilities exceed assets by " f"${abs(net_worth):,.2f}."
                ),
                category=CoachingCategory.NET_WORTH,
                severity=InsightSeverity.WARNING,
                metric=METRIC_NET_WORTH,
                current_value=float(net_worth),
                benchmark_value=0.0,
                action=(
                    "Prioritize debt reduction and consistent " "asset accumulation."
                ),
            )
        ]

    return [
        FinancialCoachInsight(
            key="net_worth:positive",
            title="Positive Net Worth",
            message=(f"Current estimated net worth is " f"${net_worth:,.2f}."),
            category=CoachingCategory.NET_WORTH,
            severity=InsightSeverity.POSITIVE,
            metric=METRIC_NET_WORTH,
            current_value=float(net_worth),
            benchmark_value=0.0,
            action=(
                "Continue increasing assets while reducing " "high-cost liabilities."
            ),
        )
    ]


def build_health_score_insights(
    snapshot: dict,
) -> list[FinancialCoachInsight]:
    """Build insights related to the financial health score."""
    health_score = _to_float(
        snapshot.get(
            "health_score",
            0.0,
        )
    )

    health_status = str(
        snapshot.get(
            "health_status",
            "Unknown",
        )
    ).strip()

    if health_score < HEALTH_SCORE_CRITICAL_THRESHOLD:
        severity = InsightSeverity.CRITICAL
        action = (
            "Address negative cash flow, debt pressure, "
            "and insufficient reserves immediately."
        )

    elif health_score < HEALTH_SCORE_WARNING_THRESHOLD:
        severity = InsightSeverity.WARNING
        action = "Focus on the highest-priority weakness in the " "financial snapshot."

    elif health_score < HEALTH_SCORE_INFORMATIONAL_THRESHOLD:
        severity = InsightSeverity.INFORMATIONAL
        action = "Continue improving savings, debt, and cash-flow " "metrics."

    else:
        severity = InsightSeverity.POSITIVE
        action = (
            "Maintain current progress and strengthen " "long-term financial goals."
        )

    return [
        FinancialCoachInsight(
            key="financial_health:score",
            title="Financial Health Assessment",
            message=(
                f"The current financial health score is "
                f"{health_score:.0f}/100 "
                f"({health_status})."
            ),
            category=CoachingCategory.FINANCIAL_HEALTH,
            severity=severity,
            metric="Financial Health Score",
            current_value=health_score,
            benchmark_value=float(HEALTH_SCORE_INFORMATIONAL_THRESHOLD),
            action=action,
        )
    ]


def generate_financial_coach_insights(
    snapshot: dict,
) -> list[FinancialCoachInsight]:
    """Generate and prioritize coaching insights."""
    insights: list[FinancialCoachInsight] = []

    insights.extend(build_cash_flow_insights(snapshot))
    insights.extend(build_savings_rate_insights(snapshot))
    insights.extend(build_emergency_fund_insights(snapshot))
    insights.extend(build_debt_insights(snapshot))
    insights.extend(build_spending_insights(snapshot))
    insights.extend(build_net_worth_insights(snapshot))
    insights.extend(build_health_score_insights(snapshot))

    severity_order = {
        InsightSeverity.CRITICAL: 0,
        InsightSeverity.WARNING: 1,
        InsightSeverity.INFORMATIONAL: 2,
        InsightSeverity.POSITIVE: 3,
    }

    insights.sort(
        key=lambda insight: (
            severity_order[insight.severity],
            insight.category.value.lower(),
            insight.title.lower(),
        )
    )

    return insights

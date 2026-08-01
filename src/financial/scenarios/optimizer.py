from dataclasses import dataclass, field

from src.core.exceptions import ValidationError
from src.core.money import ZERO, to_money
from src.financial.scenarios.factory import (
    register_default_scenario_handlers,
)
from src.financial.scenarios.models import (
    ScenarioRequest,
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.ranking import (
    RankedScenario,
    ScenarioRankingMetric,
    rank_scenarios,
)
from src.financial.scenarios.service import (
    ScenarioService,
    scenario_service,
)


DEFAULT_EXPENSE_REDUCTION_PERCENTAGES = (
    10.0,
    15.0,
    20.0,
)

DEFAULT_INCOME_INCREASE_PERCENTAGES = (
    5.0,
    10.0,
    15.0,
)

DEFAULT_ADDITIONAL_SAVINGS_AMOUNTS = (
    100.0,
    250.0,
    500.0,
)

DEFAULT_EXTRA_DEBT_PAYMENTS = (
    100.0,
    250.0,
    500.0,
)


@dataclass(frozen=True)
class OptimizationCandidate:
    """Represents one generated optimization candidate."""

    request: ScenarioRequest
    source: str
    rationale: str

    def __post_init__(self) -> None:
        """Validate and normalize candidate metadata."""
        normalized_source = self.source.strip()
        normalized_rationale = self.rationale.strip()

        if not normalized_source:
            raise ValidationError("Optimization candidate source cannot be empty.")

        if not normalized_rationale:
            raise ValidationError("Optimization candidate rationale cannot be empty.")

        object.__setattr__(
            self,
            "source",
            normalized_source,
        )

        object.__setattr__(
            self,
            "rationale",
            normalized_rationale,
        )

    def to_dict(self) -> dict:
        """Convert the optimization candidate to a dictionary."""
        return {
            "request": self.request.to_dict(),
            "source": self.source,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class OptimizationFailure:
    """Represents a candidate that could not be evaluated."""

    candidate_name: str
    error: str

    def __post_init__(self) -> None:
        """Validate and normalize failure data."""
        normalized_name = self.candidate_name.strip()
        normalized_error = self.error.strip()

        if not normalized_name:
            raise ValidationError("Optimization failure candidate name cannot be empty.")

        if not normalized_error:
            raise ValidationError("Optimization failure error cannot be empty.")

        object.__setattr__(
            self,
            "candidate_name",
            normalized_name,
        )

        object.__setattr__(
            self,
            "error",
            normalized_error,
        )

    def to_dict(self) -> dict:
        """Convert the failure to a dictionary."""
        return {
            "candidate_name": self.candidate_name,
            "error": self.error,
        }


@dataclass(frozen=True)
class OptimizationResult:
    """Represents a completed financial optimization run."""

    snapshot: dict
    candidates: list[OptimizationCandidate]
    successful_results: list[ScenarioResult]
    ranked_scenarios: list[RankedScenario]
    failures: list[OptimizationFailure] = field(
        default_factory=list,
    )
    ranking_metric: ScenarioRankingMetric = ScenarioRankingMetric.OVERALL

    def __post_init__(self) -> None:
        """Protect mutable optimization collections."""
        object.__setattr__(
            self,
            "snapshot",
            self.snapshot.copy(),
        )

        object.__setattr__(
            self,
            "candidates",
            self.candidates.copy(),
        )

        object.__setattr__(
            self,
            "successful_results",
            self.successful_results.copy(),
        )

        object.__setattr__(
            self,
            "ranked_scenarios",
            self.ranked_scenarios.copy(),
        )

        object.__setattr__(
            self,
            "failures",
            self.failures.copy(),
        )

    @property
    def best_scenario(
        self,
    ) -> RankedScenario | None:
        """Return the highest-ranked successful scenario."""
        if not self.ranked_scenarios:
            return None

        return self.ranked_scenarios[0]

    @property
    def candidate_count(
        self,
    ) -> int:
        """Return the number of generated candidates."""
        return len(self.candidates)

    @property
    def success_count(
        self,
    ) -> int:
        """Return the number of successful candidates."""
        return len(self.successful_results)

    @property
    def failure_count(
        self,
    ) -> int:
        """Return the number of failed candidates."""
        return len(self.failures)

    def to_dict(self) -> dict:
        """Convert the optimization result to a dictionary."""
        return {
            "snapshot": self.snapshot.copy(),
            "ranking_metric": self.ranking_metric.value,
            "candidate_count": self.candidate_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "successful_results": [
                result.to_dict() for result in self.successful_results
            ],
            "ranked_scenarios": [ranked.to_dict() for ranked in self.ranked_scenarios],
            "failures": [failure.to_dict() for failure in self.failures],
            "best_scenario": (
                self.best_scenario.to_dict() if self.best_scenario is not None else None
            ),
        }


def _normalize_positive_values(
    values: tuple[float, ...],
) -> tuple[float, ...]:
    """Return unique positive values in original order."""
    normalized: list[float] = []
    seen: set[float] = set()

    for value in values:
        numeric_value = float(value)

        if numeric_value <= 0:
            continue

        if numeric_value in seen:
            continue

        seen.add(numeric_value)
        normalized.append(numeric_value)

    return tuple(normalized)


def _build_expense_candidates(
    snapshot: dict,
    percentages: tuple[float, ...],
    horizon_months: int,
) -> list[OptimizationCandidate]:
    """Generate expense-reduction candidates."""
    category_totals = snapshot.get(
        "category_totals",
        {},
    )

    if not isinstance(category_totals, dict):
        return []

    candidates: list[OptimizationCandidate] = []

    sorted_categories = sorted(
        category_totals.items(),
        key=lambda item: (
            -to_money(item[1]),
            str(item[0]).lower(),
        ),
    )

    for category, total in sorted_categories:
        category_name = str(category).strip()
        category_total = to_money(total)

        if not category_name or category_total <= 0:
            continue

        for percentage in percentages:
            candidates.append(
                OptimizationCandidate(
                    request=ScenarioRequest(
                        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
                        name=(f"Reduce {category_name} " f"by {percentage:g}%"),
                        description=(
                            f"Reduce monthly {category_name} "
                            f"spending by {percentage:g} percent."
                        ),
                        parameters={
                            "category": category_name,
                            "reduction_percentage": percentage,
                            "horizon_months": horizon_months,
                        },
                    ),
                    source="Expense Optimization",
                    rationale=(
                        f"{category_name} currently represents "
                        f"${category_total:,.2f} in monthly spending."
                    ),
                )
            )

    return candidates


def _build_income_candidates(
    snapshot: dict,
    percentages: tuple[float, ...],
    horizon_months: int,
) -> list[OptimizationCandidate]:
    """Generate income-increase candidates."""
    total_income = to_money(
        snapshot.get(
            "total_income",
            ZERO,
        )
    )

    if total_income <= 0:
        return []

    candidates: list[OptimizationCandidate] = []

    for percentage in percentages:
        candidates.append(
            OptimizationCandidate(
                request=ScenarioRequest(
                    scenario_type=(ScenarioType.INCOME_INCREASE),
                    name=(f"Increase Income by " f"{percentage:g}%"),
                    description=(
                        f"Model a {percentage:g} percent " "increase in monthly income."
                    ),
                    parameters={
                        "increase_percentage": percentage,
                        "horizon_months": horizon_months,
                    },
                ),
                source="Income Optimization",
                rationale=(
                    "Higher income may improve cash flow, "
                    "savings capacity, and net worth."
                ),
            )
        )

    return candidates


def _build_savings_candidates(
    snapshot: dict,
    amounts: tuple[float, ...],
    horizon_months: int,
) -> list[OptimizationCandidate]:
    """Generate additional-savings candidates."""
    net_cash_flow = to_money(
        snapshot.get(
            "net_cash_flow",
            ZERO,
        )
    )

    if net_cash_flow <= 0:
        return []

    candidates: list[OptimizationCandidate] = []

    for amount in amounts:
        if amount > net_cash_flow:
            continue

        candidates.append(
            OptimizationCandidate(
                request=ScenarioRequest(
                    scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
                    name=(f"Save an Additional " f"${amount:,.2f} Monthly"),
                    description=(
                        f"Direct an additional "
                        f"${amount:,.2f} to savings each month."
                    ),
                    parameters={
                        "additional_monthly_savings": amount,
                        "horizon_months": horizon_months,
                    },
                ),
                source="Savings Optimization",
                rationale=(
                    f"The current monthly net cash flow is " f"${net_cash_flow:,.2f}."
                ),
            )
        )

    return candidates


def _build_debt_candidates(
    snapshot: dict,
    amounts: tuple[float, ...],
    horizon_months: int,
) -> list[OptimizationCandidate]:
    """Generate extra-debt-payment candidates."""
    debts = snapshot.get(
        "debts",
        [],
    )

    if not isinstance(debts, list):
        return []

    net_cash_flow = to_money(
        snapshot.get(
            "net_cash_flow",
            ZERO,
        )
    )

    candidates: list[OptimizationCandidate] = []

    sorted_debts = sorted(
        debts,
        key=lambda debt: (
            -float(
                debt.get(
                    "interest_rate",
                    0.0,
                )
            ),
            -to_money(
                debt.get(
                    "balance",
                    ZERO,
                )
            ),
        ),
    )

    for debt in sorted_debts:
        try:
            debt_id = int(debt["id"])
            debt_name = str(debt["name"]).strip()
            balance = to_money(debt["balance"])
            interest_rate = float(debt["interest_rate"])
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

        if not debt_name or balance <= 0:
            continue

        for amount in amounts:
            if net_cash_flow > 0 and amount > net_cash_flow:
                continue

            candidates.append(
                OptimizationCandidate(
                    request=ScenarioRequest(
                        scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
                        name=(
                            f"Pay an Extra " f"${amount:,.2f} toward " f"{debt_name}"
                        ),
                        description=(
                            f"Apply an additional "
                            f"${amount:,.2f} per month "
                            f"to {debt_name}."
                        ),
                        parameters={
                            "debt_id": debt_id,
                            "extra_monthly_payment": amount,
                            "horizon_months": horizon_months,
                        },
                    ),
                    source="Debt Optimization",
                    rationale=(
                        f"{debt_name} has a "
                        f"{interest_rate:.2f}% interest rate "
                        f"and a ${balance:,.2f} balance."
                    ),
                )
            )

    return candidates


def generate_optimization_candidates(
    snapshot: dict,
    *,
    horizon_months: int = 12,
    expense_reduction_percentages: tuple[
        float, ...
    ] = DEFAULT_EXPENSE_REDUCTION_PERCENTAGES,
    income_increase_percentages: tuple[
        float, ...
    ] = DEFAULT_INCOME_INCREASE_PERCENTAGES,
    additional_savings_amounts: tuple[float, ...] = DEFAULT_ADDITIONAL_SAVINGS_AMOUNTS,
    extra_debt_payments: tuple[float, ...] = DEFAULT_EXTRA_DEBT_PAYMENTS,
) -> list[OptimizationCandidate]:
    """Generate candidate scenarios from a financial snapshot."""
    if horizon_months <= 0:
        raise ValidationError("Optimization horizon must be greater than zero months.")

    normalized_expense_percentages = _normalize_positive_values(
        expense_reduction_percentages
    )

    normalized_income_percentages = _normalize_positive_values(
        income_increase_percentages
    )

    normalized_savings_amounts = _normalize_positive_values(additional_savings_amounts)

    normalized_debt_payments = _normalize_positive_values(extra_debt_payments)

    candidates: list[OptimizationCandidate] = []

    candidates.extend(
        _build_expense_candidates(
            snapshot,
            normalized_expense_percentages,
            horizon_months,
        )
    )

    candidates.extend(
        _build_income_candidates(
            snapshot,
            normalized_income_percentages,
            horizon_months,
        )
    )

    candidates.extend(
        _build_savings_candidates(
            snapshot,
            normalized_savings_amounts,
            horizon_months,
        )
    )

    candidates.extend(
        _build_debt_candidates(
            snapshot,
            normalized_debt_payments,
            horizon_months,
        )
    )

    return candidates


def optimize_financial_snapshot(
    snapshot: dict,
    *,
    limit: int | None = None,
    ranking_metric: ScenarioRankingMetric = (ScenarioRankingMetric.OVERALL),
    horizon_months: int = 12,
    service: ScenarioService | None = None,
    register_handlers: bool = True,
    expense_reduction_percentages: tuple[
        float, ...
    ] = DEFAULT_EXPENSE_REDUCTION_PERCENTAGES,
    income_increase_percentages: tuple[
        float, ...
    ] = DEFAULT_INCOME_INCREASE_PERCENTAGES,
    additional_savings_amounts: tuple[float, ...] = DEFAULT_ADDITIONAL_SAVINGS_AMOUNTS,
    extra_debt_payments: tuple[float, ...] = DEFAULT_EXTRA_DEBT_PAYMENTS,
) -> OptimizationResult:
    """Generate, evaluate, score, and rank candidate scenarios."""
    if limit is not None and limit <= 0:
        raise ValidationError("Optimization result limit must be greater than zero.")

    active_service = service if service is not None else scenario_service

    if service is None and register_handlers:
        register_default_scenario_handlers()

    candidates = generate_optimization_candidates(
        snapshot,
        horizon_months=horizon_months,
        expense_reduction_percentages=(expense_reduction_percentages),
        income_increase_percentages=(income_increase_percentages),
        additional_savings_amounts=(additional_savings_amounts),
        extra_debt_payments=(extra_debt_payments),
    )

    successful_results: list[ScenarioResult] = []

    failures: list[OptimizationFailure] = []

    for candidate in candidates:
        try:
            result = active_service.run(
                request=candidate.request,
                snapshot=snapshot,
            )
        except ValueError as error:
            failures.append(
                OptimizationFailure(
                    candidate_name=(candidate.request.name),
                    error=str(error),
                )
            )
            continue

        successful_results.append(result)

    ranked_scenarios = rank_scenarios(
        successful_results,
        ranking_metric,
    )

    if limit is not None:
        ranked_scenarios = ranked_scenarios[:limit]

    return OptimizationResult(
        snapshot=snapshot,
        candidates=candidates,
        successful_results=successful_results,
        ranked_scenarios=ranked_scenarios,
        failures=failures,
        ranking_metric=ranking_metric,
    )

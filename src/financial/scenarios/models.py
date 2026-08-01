from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any


def _to_decimal(value: Decimal | float | int | str) -> Decimal:
    """
    Convert a numeric impact value to Decimal without currency rounding.

    ScenarioImpact represents a mix of currency amounts and non-currency
    metrics (percentages, month counts), so it preserves full precision
    rather than quantizing to two decimal places like core.money.to_money.
    """
    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(str(value))

    return Decimal(value.strip())


class ScenarioType(Enum):
    """Supported financial scenario types."""

    EXPENSE_REDUCTION = "Expense Reduction"
    INCOME_INCREASE = "Income Increase"
    EXTRA_DEBT_PAYMENT = "Extra Debt Payment"
    ADDITIONAL_SAVINGS = "Additional Savings"


@dataclass(frozen=True)
class ScenarioAssumption:
    """Represents one assumption used by a scenario."""

    name: str
    value: Decimal | float | int | str
    description: str = ""

    def __post_init__(self) -> None:
        """Validate and normalize the assumption."""
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError("Scenario assumption name cannot be empty.")

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )

        object.__setattr__(
            self,
            "description",
            self.description.strip(),
        )

    def to_dict(self) -> dict:
        """Convert the assumption to a dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "description": self.description,
        }


@dataclass(frozen=True)
class ScenarioImpact:
    """Represents one measured scenario impact."""

    metric: str
    original_value: Decimal
    projected_value: Decimal
    change: Decimal

    def __post_init__(self) -> None:
        """Validate and normalize the impact."""
        normalized_metric = self.metric.strip()

        if not normalized_metric:
            raise ValueError("Scenario impact metric cannot be empty.")

        object.__setattr__(
            self,
            "metric",
            normalized_metric,
        )

    @classmethod
    def create(
        cls,
        metric: str,
        original_value: Decimal | float | int | str,
        projected_value: Decimal | float | int | str,
    ) -> "ScenarioImpact":
        """Create an impact and calculate its change."""
        normalized_original = _to_decimal(original_value)
        normalized_projected = _to_decimal(projected_value)

        return cls(
            metric=metric,
            original_value=normalized_original,
            projected_value=normalized_projected,
            change=(normalized_projected - normalized_original),
        )

    def to_dict(self) -> dict:
        """Convert the impact to a dictionary."""
        return {
            "metric": self.metric,
            "original_value": str(self.original_value),
            "projected_value": str(self.projected_value),
            "change": str(self.change),
        }


@dataclass(frozen=True)
class ScenarioRequest:
    """Represents a request to run one financial scenario."""

    scenario_type: ScenarioType
    name: str
    description: str
    parameters: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate and normalize the request."""
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError("Scenario request name cannot be empty.")

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )

        object.__setattr__(
            self,
            "description",
            self.description.strip(),
        )

        object.__setattr__(
            self,
            "parameters",
            self.parameters.copy(),
        )

    def to_dict(self) -> dict:
        """Convert the request to a dictionary."""
        return {
            "scenario_type": self.scenario_type.name,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters.copy(),
        }


@dataclass(frozen=True)
class ScenarioResult:
    """Represents the complete result of a scenario."""

    scenario_type: ScenarioType
    name: str
    description: str
    assumptions: list[ScenarioAssumption]
    original_snapshot: dict
    projected_snapshot: dict
    impacts: list[ScenarioImpact]
    benefits: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate and protect mutable scenario data."""
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError("Scenario result name cannot be empty.")

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )

        object.__setattr__(
            self,
            "description",
            self.description.strip(),
        )

        object.__setattr__(
            self,
            "assumptions",
            self.assumptions.copy(),
        )

        object.__setattr__(
            self,
            "original_snapshot",
            self.original_snapshot.copy(),
        )

        object.__setattr__(
            self,
            "projected_snapshot",
            self.projected_snapshot.copy(),
        )

        object.__setattr__(
            self,
            "impacts",
            self.impacts.copy(),
        )

        object.__setattr__(
            self,
            "benefits",
            [benefit.strip() for benefit in self.benefits if benefit.strip()],
        )

        object.__setattr__(
            self,
            "risks",
            [risk.strip() for risk in self.risks if risk.strip()],
        )

        object.__setattr__(
            self,
            "recommendations",
            [
                recommendation.strip()
                for recommendation in self.recommendations
                if recommendation.strip()
            ],
        )

    def get_impact(
        self,
        metric: str,
    ) -> ScenarioImpact | None:
        """Return an impact by metric name."""
        normalized_metric = metric.strip().lower()

        for impact in self.impacts:
            if impact.metric.lower() == normalized_metric:
                return impact

        return None

    def to_dict(self) -> dict:
        """Convert the complete result to a dictionary."""
        return {
            "scenario_type": self.scenario_type.name,
            "name": self.name,
            "description": self.description,
            "assumptions": [assumption.to_dict() for assumption in self.assumptions],
            "original_snapshot": (self.original_snapshot.copy()),
            "projected_snapshot": (self.projected_snapshot.copy()),
            "impacts": [impact.to_dict() for impact in self.impacts],
            "benefits": self.benefits.copy(),
            "risks": self.risks.copy(),
            "recommendations": (self.recommendations.copy()),
        }

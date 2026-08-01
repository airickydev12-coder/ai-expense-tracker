"""Models for financial-goal planning and feasibility."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from src.core.exceptions import ValidationError
from src.core.money import (
    ZERO,
    money_to_json,
    to_money,
)


class GoalFeasibilityStatus(Enum):
    """Status assigned to a financial goal plan."""

    COMPLETED = "Completed"
    FEASIBLE = "Feasible"
    AT_RISK = "At Risk"
    UNFUNDED = "Unfunded"
    MISSED_DEADLINE = "Missed Deadline"


@dataclass(frozen=True)
class GoalProjection:
    """Represents projected progress for one financial goal."""

    goal_id: int
    goal_name: str
    as_of_date: date
    target_date: date
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    months_remaining: int
    required_monthly_contribution: Decimal
    planned_monthly_contribution: Decimal
    monthly_contribution_difference: Decimal
    projected_completion_date: date | None

    def __post_init__(self) -> None:
        """Validate and normalize projection data."""
        normalized_name = self.goal_name.strip()

        normalized_target_amount = to_money(self.target_amount)
        normalized_current_amount = to_money(self.current_amount)
        normalized_remaining_amount = to_money(self.remaining_amount)
        normalized_required_contribution = to_money(self.required_monthly_contribution)
        normalized_planned_contribution = to_money(self.planned_monthly_contribution)
        normalized_contribution_difference = to_money(
            self.monthly_contribution_difference
        )

        if self.goal_id <= 0:
            raise ValidationError("Goal projection ID must be greater than zero.")

        if not normalized_name:
            raise ValidationError("Goal projection name cannot be empty.")

        if normalized_target_amount <= ZERO:
            raise ValidationError(
                "Goal projection target amount must be " "greater than zero."
            )

        if normalized_current_amount < ZERO:
            raise ValidationError("Goal projection current amount cannot be negative.")

        if normalized_remaining_amount < ZERO:
            raise ValidationError(
                "Goal projection remaining amount cannot be negative."
            )

        if self.months_remaining < 0:
            raise ValidationError(
                "Goal projection months remaining cannot be negative."
            )

        if normalized_required_contribution < ZERO:
            raise ValidationError("Required monthly contribution cannot be negative.")

        if normalized_planned_contribution < ZERO:
            raise ValidationError("Planned monthly contribution cannot be negative.")

        object.__setattr__(
            self,
            "goal_name",
            normalized_name,
        )
        object.__setattr__(
            self,
            "target_amount",
            normalized_target_amount,
        )
        object.__setattr__(
            self,
            "current_amount",
            normalized_current_amount,
        )
        object.__setattr__(
            self,
            "remaining_amount",
            normalized_remaining_amount,
        )
        object.__setattr__(
            self,
            "required_monthly_contribution",
            normalized_required_contribution,
        )
        object.__setattr__(
            self,
            "planned_monthly_contribution",
            normalized_planned_contribution,
        )
        object.__setattr__(
            self,
            "monthly_contribution_difference",
            normalized_contribution_difference,
        )

    @property
    def is_complete(self) -> bool:
        """Return whether the goal is fully funded."""
        return self.remaining_amount <= ZERO

    @property
    def has_deadline_passed(self) -> bool:
        """Return whether the target date has passed."""
        return not self.is_complete and self.target_date <= self.as_of_date

    @property
    def monthly_shortfall(self) -> Decimal:
        """Return the monthly contribution shortfall."""
        shortfall = (
            self.required_monthly_contribution - self.planned_monthly_contribution
        )

        return max(
            shortfall,
            ZERO,
        )

    @property
    def monthly_surplus(self) -> Decimal:
        """Return the monthly contribution surplus."""
        surplus = self.planned_monthly_contribution - self.required_monthly_contribution

        return max(
            surplus,
            ZERO,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the projection to a JSON-safe dictionary."""
        return {
            "goal_id": self.goal_id,
            "goal_name": self.goal_name,
            "as_of_date": self.as_of_date.isoformat(),
            "target_date": self.target_date.isoformat(),
            "target_amount": money_to_json(self.target_amount),
            "current_amount": money_to_json(self.current_amount),
            "remaining_amount": money_to_json(self.remaining_amount),
            "months_remaining": self.months_remaining,
            "required_monthly_contribution": money_to_json(
                self.required_monthly_contribution
            ),
            "planned_monthly_contribution": money_to_json(
                self.planned_monthly_contribution
            ),
            "monthly_contribution_difference": money_to_json(
                self.monthly_contribution_difference
            ),
            "monthly_shortfall": money_to_json(self.monthly_shortfall),
            "monthly_surplus": money_to_json(self.monthly_surplus),
            "projected_completion_date": (
                self.projected_completion_date.isoformat()
                if self.projected_completion_date is not None
                else None
            ),
            "is_complete": self.is_complete,
            "has_deadline_passed": self.has_deadline_passed,
        }


@dataclass(frozen=True)
class GoalFeasibilityAssessment:
    """Represents the feasibility assessment for one goal."""

    projection: GoalProjection
    status: GoalFeasibilityStatus
    is_feasible: bool
    summary: str
    recommendation: str

    def __post_init__(self) -> None:
        """Validate and normalize assessment text."""
        normalized_summary = self.summary.strip()
        normalized_recommendation = self.recommendation.strip()

        if not isinstance(
            self.projection,
            GoalProjection,
        ):
            raise TypeError(
                "Goal feasibility projection must be " "a GoalProjection instance."
            )

        if not isinstance(
            self.status,
            GoalFeasibilityStatus,
        ):
            raise TypeError(
                "Goal feasibility status must be " "a GoalFeasibilityStatus."
            )

        if not normalized_summary:
            raise ValidationError("Goal feasibility summary cannot be empty.")

        if not normalized_recommendation:
            raise ValidationError("Goal feasibility recommendation cannot be empty.")

        object.__setattr__(
            self,
            "summary",
            normalized_summary,
        )
        object.__setattr__(
            self,
            "recommendation",
            normalized_recommendation,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the feasibility assessment to a dictionary."""
        return {
            "projection": self.projection.to_dict(),
            "status": self.status.value,
            "is_feasible": self.is_feasible,
            "summary": self.summary,
            "recommendation": self.recommendation,
        }

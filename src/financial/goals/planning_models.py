from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any


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
    target_amount: float
    current_amount: float
    remaining_amount: float
    months_remaining: int
    required_monthly_contribution: float
    planned_monthly_contribution: float
    monthly_contribution_difference: float
    projected_completion_date: date | None

    def __post_init__(self) -> None:
        """Validate and normalize projection data."""
        normalized_name = self.goal_name.strip()

        if self.goal_id <= 0:
            raise ValueError("Goal projection ID must be greater than zero.")

        if not normalized_name:
            raise ValueError("Goal projection name cannot be empty.")

        if self.target_amount <= 0:
            raise ValueError(
                "Goal projection target amount must be " "greater than zero."
            )

        if self.current_amount < 0:
            raise ValueError("Goal projection current amount cannot be negative.")

        if self.remaining_amount < 0:
            raise ValueError("Goal projection remaining amount cannot be negative.")

        if self.months_remaining < 0:
            raise ValueError("Goal projection months remaining cannot be negative.")

        if self.required_monthly_contribution < 0:
            raise ValueError("Required monthly contribution cannot be negative.")

        if self.planned_monthly_contribution < 0:
            raise ValueError("Planned monthly contribution cannot be negative.")

        object.__setattr__(
            self,
            "goal_name",
            normalized_name,
        )

    @property
    def is_complete(self) -> bool:
        """Return whether the goal is fully funded."""
        return self.remaining_amount <= 0

    @property
    def has_deadline_passed(self) -> bool:
        """Return whether the target date has passed."""
        return not self.is_complete and self.target_date <= self.as_of_date

    @property
    def monthly_shortfall(self) -> float:
        """Return the monthly contribution shortfall."""
        return max(
            self.required_monthly_contribution - self.planned_monthly_contribution,
            0.0,
        )

    @property
    def monthly_surplus(self) -> float:
        """Return the monthly contribution surplus."""
        return max(
            self.planned_monthly_contribution - self.required_monthly_contribution,
            0.0,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the projection to a dictionary."""
        return {
            "goal_id": self.goal_id,
            "goal_name": self.goal_name,
            "as_of_date": self.as_of_date.isoformat(),
            "target_date": self.target_date.isoformat(),
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "remaining_amount": self.remaining_amount,
            "months_remaining": self.months_remaining,
            "required_monthly_contribution": (self.required_monthly_contribution),
            "planned_monthly_contribution": (self.planned_monthly_contribution),
            "monthly_contribution_difference": (self.monthly_contribution_difference),
            "monthly_shortfall": self.monthly_shortfall,
            "monthly_surplus": self.monthly_surplus,
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

        if not normalized_summary:
            raise ValueError("Goal feasibility summary cannot be empty.")

        if not normalized_recommendation:
            raise ValueError("Goal feasibility recommendation cannot be empty.")

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

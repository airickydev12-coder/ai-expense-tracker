from dataclasses import dataclass, field
from enum import Enum

from src.core.exceptions import ValidationError


class CoachingPriority(Enum):
    """Priority assigned to a coaching recommendation."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CoachingCategory(Enum):
    """Financial category associated with coaching advice."""

    CASH_FLOW = "Cash Flow"
    DEBT = "Debt"
    SAVINGS = "Savings"
    SPENDING = "Spending"
    INCOME = "Income"
    FINANCIAL_HEALTH = "Financial Health"
    GENERAL = "General"


@dataclass(frozen=True)
class CoachingAdvice:
    """Represents one actionable financial coaching recommendation."""

    key: str
    title: str
    message: str
    action: str
    reason: str
    priority: CoachingPriority
    category: CoachingCategory
    expected_impact: str = ""
    source_scenario: str = ""
    score: float | None = None
    warnings: list[str] = field(
        default_factory=list,
    )

    def __post_init__(self) -> None:
        """Validate and normalize coaching advice."""
        normalized_key = self.key.strip()
        normalized_title = self.title.strip()
        normalized_message = self.message.strip()
        normalized_action = self.action.strip()
        normalized_reason = self.reason.strip()

        if not normalized_key:
            raise ValidationError("Coaching advice key cannot be empty.")

        if not normalized_title:
            raise ValidationError("Coaching advice title cannot be empty.")

        if not normalized_message:
            raise ValidationError("Coaching advice message cannot be empty.")

        if not normalized_action:
            raise ValidationError("Coaching advice action cannot be empty.")

        if not normalized_reason:
            raise ValidationError("Coaching advice reason cannot be empty.")

        if self.score is not None and (self.score < 0 or self.score > 100):
            raise ValidationError("Coaching advice score must be between 0 and 100.")

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
            "action",
            normalized_action,
        )
        object.__setattr__(
            self,
            "reason",
            normalized_reason,
        )
        object.__setattr__(
            self,
            "expected_impact",
            self.expected_impact.strip(),
        )
        object.__setattr__(
            self,
            "source_scenario",
            self.source_scenario.strip(),
        )
        object.__setattr__(
            self,
            "warnings",
            _clean_strings(self.warnings),
        )

    def to_dict(self) -> dict:
        """Convert coaching advice to a dictionary."""
        return {
            "key": self.key,
            "title": self.title,
            "message": self.message,
            "action": self.action,
            "reason": self.reason,
            "priority": self.priority.value,
            "category": self.category.value,
            "expected_impact": self.expected_impact,
            "source_scenario": self.source_scenario,
            "score": self.score,
            "warnings": self.warnings.copy(),
        }


@dataclass(frozen=True)
class AdviceExplanation:
    """Represents a plain-language explanation of coaching advice."""

    advice_key: str
    summary: str
    why_it_matters: str
    projected_effects: list[str]
    assumptions: list[str]
    risks: list[str]

    def __post_init__(self) -> None:
        """Validate and protect explanation data."""
        normalized_key = self.advice_key.strip()
        normalized_summary = self.summary.strip()
        normalized_why = self.why_it_matters.strip()

        if not normalized_key:
            raise ValidationError("Advice explanation key cannot be empty.")

        if not normalized_summary:
            raise ValidationError("Advice explanation summary cannot be empty.")

        if not normalized_why:
            raise ValidationError(
                "Advice explanation must state why the advice matters."
            )

        object.__setattr__(
            self,
            "advice_key",
            normalized_key,
        )
        object.__setattr__(
            self,
            "summary",
            normalized_summary,
        )
        object.__setattr__(
            self,
            "why_it_matters",
            normalized_why,
        )
        object.__setattr__(
            self,
            "projected_effects",
            _clean_strings(self.projected_effects),
        )
        object.__setattr__(
            self,
            "assumptions",
            _clean_strings(self.assumptions),
        )
        object.__setattr__(
            self,
            "risks",
            _clean_strings(self.risks),
        )

    def to_dict(self) -> dict:
        """Convert the explanation to a dictionary."""
        return {
            "advice_key": self.advice_key,
            "summary": self.summary,
            "why_it_matters": self.why_it_matters,
            "projected_effects": (self.projected_effects.copy()),
            "assumptions": self.assumptions.copy(),
            "risks": self.risks.copy(),
        }


def _clean_strings(
    values: list[str],
) -> list[str]:
    """Normalize and deduplicate strings."""
    cleaned: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = value.strip()

        if not normalized:
            continue

        key = normalized.lower()

        if key in seen:
            continue

        seen.add(key)
        cleaned.append(normalized)

    return cleaned

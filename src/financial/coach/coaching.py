from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.financial.coach.advisor import (
    generate_optimizer_advice,
)
from src.financial.coach.explanation import (
    explain_coaching_advice,
)
from src.financial.coach.insights import (
    FinancialCoachInsight,
    InsightSeverity,
    generate_financial_coach_insights,
)
from src.financial.coach.models import (
    AdviceExplanation,
    CoachingAdvice,
)
from src.financial.scenarios.optimizer import (
    OptimizationResult,
)


@dataclass(frozen=True)
class CoachingSession:
    """Represents a complete deterministic financial coaching session."""

    generated_at: datetime
    financial_health_score: float
    financial_health_status: str
    summary: str
    _advice: tuple[CoachingAdvice, ...]
    _explanations: tuple[AdviceExplanation, ...]
    _insights: tuple[FinancialCoachInsight, ...]
    _next_steps: tuple[str, ...]
    _warnings: tuple[str, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self) -> None:
        """Validate and protect coaching-session data."""
        normalized_status = self.financial_health_status.strip()
        normalized_summary = self.summary.strip()

        if not normalized_status:
            raise ValueError("Financial health status cannot be empty.")

        if not normalized_summary:
            raise ValueError("Coaching session summary cannot be empty.")

        object.__setattr__(
            self,
            "financial_health_status",
            normalized_status,
        )
        object.__setattr__(
            self,
            "summary",
            normalized_summary,
        )
        object.__setattr__(
            self,
            "_advice",
            tuple(self._advice),
        )
        object.__setattr__(
            self,
            "_explanations",
            tuple(self._explanations),
        )
        object.__setattr__(
            self,
            "_insights",
            tuple(self._insights),
        )
        object.__setattr__(
            self,
            "_next_steps",
            tuple(_clean_strings(list(self._next_steps))),
        )
        object.__setattr__(
            self,
            "_warnings",
            tuple(_clean_strings(list(self._warnings))),
        )

    @property
    def advice(
        self,
    ) -> list[CoachingAdvice]:
        """Return a copy of the coaching advice."""
        return list(self._advice)

    @property
    def explanations(
        self,
    ) -> list[AdviceExplanation]:
        """Return a copy of the advice explanations."""
        return list(self._explanations)

    @property
    def insights(
        self,
    ) -> list[FinancialCoachInsight]:
        """Return a copy of the coaching insights."""
        return list(self._insights)

    @property
    def next_steps(
        self,
    ) -> list[str]:
        """Return a copy of the recommended next steps."""
        return list(self._next_steps)

    @property
    def warnings(
        self,
    ) -> list[str]:
        """Return a copy of the coaching warnings."""
        return list(self._warnings)

    @property
    def top_advice(
        self,
    ) -> CoachingAdvice | None:
        """Return the highest-priority coaching advice."""
        if not self._advice:
            return None

        return self._advice[0]

    @property
    def critical_insights(
        self,
    ) -> list[FinancialCoachInsight]:
        """Return all critical coaching insights."""
        return [
            insight
            for insight in self._insights
            if (insight.severity == InsightSeverity.CRITICAL)
        ]

    def get_explanation(
        self,
        advice_key: str,
    ) -> AdviceExplanation | None:
        """Return an explanation by coaching-advice key."""
        normalized_key = advice_key.strip().lower()

        for explanation in self._explanations:
            if explanation.advice_key.lower() == normalized_key:
                return explanation

        return None

    def to_dict(self) -> dict:
        """Convert the coaching session to a dictionary."""
        return {
            "generated_at": (self.generated_at.isoformat()),
            "financial_health_score": (self.financial_health_score),
            "financial_health_status": (self.financial_health_status),
            "summary": self.summary,
            "advice": [item.to_dict() for item in self._advice],
            "explanations": [
                explanation.to_dict() for explanation in self._explanations
            ],
            "insights": [insight.to_dict() for insight in self._insights],
            "next_steps": list(self._next_steps),
            "warnings": list(self._warnings),
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


def _build_session_summary(
    snapshot: dict,
    advice: list[CoachingAdvice],
    insights: list[FinancialCoachInsight],
) -> str:
    """Build a concise coaching-session summary."""
    health_score = float(
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
    )

    critical_count = sum(
        1 for insight in insights if insight.severity == InsightSeverity.CRITICAL
    )

    warning_count = sum(
        1 for insight in insights if insight.severity == InsightSeverity.WARNING
    )

    if critical_count > 0:
        return (
            f"Financial health is {health_status} "
            f"at {health_score:.0f}/100. "
            f"The coaching analysis identified "
            f"{critical_count} critical issue"
            f"{'s' if critical_count != 1 else ''} "
            "that should be addressed first."
        )

    if advice:
        return (
            f"Financial health is {health_status} "
            f"at {health_score:.0f}/100. "
            f"The strongest recommended action is "
            f"{advice[0].title}."
        )

    if warning_count > 0:
        return (
            f"Financial health is {health_status} "
            f"at {health_score:.0f}/100. "
            f"The analysis identified "
            f"{warning_count} financial warning"
            f"{'s' if warning_count != 1 else ''}."
        )

    return (
        f"Financial health is {health_status} "
        f"at {health_score:.0f}/100. "
        "No urgent coaching actions were identified."
    )


def _build_next_steps(
    advice: list[CoachingAdvice],
    insights: list[FinancialCoachInsight],
    limit: int = 5,
) -> list[str]:
    """Build prioritized, actionable coaching steps."""
    steps: list[str] = []

    for item in advice:
        steps.append(item.action)

    for insight in insights:
        if insight.severity in {
            InsightSeverity.CRITICAL,
            InsightSeverity.WARNING,
        }:
            steps.append(insight.action)

    return _clean_strings(steps)[:limit]


def _build_warnings(
    advice: list[CoachingAdvice],
    insights: list[FinancialCoachInsight],
) -> list[str]:
    """Build combined coaching-session warnings."""
    warnings: list[str] = []

    for item in advice:
        warnings.extend(item.warnings)

    for insight in insights:
        if insight.severity in {
            InsightSeverity.CRITICAL,
            InsightSeverity.WARNING,
        }:
            warnings.append(insight.message)

    return _clean_strings(warnings)


def build_coaching_session(
    snapshot: dict,
    optimization_result: OptimizationResult,
    *,
    advice_limit: int = 3,
    next_step_limit: int = 5,
    generated_at: datetime | None = None,
) -> CoachingSession:
    """Build a complete financial coaching session."""
    if advice_limit < 0:
        raise ValueError("Advice limit cannot be negative.")

    if next_step_limit <= 0:
        raise ValueError("Next-step limit must be greater than zero.")

    advice = generate_optimizer_advice(
        optimization_result,
        limit=advice_limit,
    )

    scenario_results = {
        result.name: result for result in (optimization_result.successful_results)
    }

    explanations: list[AdviceExplanation] = []

    for item in advice:
        scenario_result = scenario_results.get(item.source_scenario)

        if scenario_result is None:
            continue

        explanations.append(
            explain_coaching_advice(
                item,
                scenario_result,
            )
        )

    insights = generate_financial_coach_insights(snapshot)

    summary = _build_session_summary(
        snapshot,
        advice,
        insights,
    )

    next_steps = _build_next_steps(
        advice,
        insights,
        limit=next_step_limit,
    )

    warnings = _build_warnings(
        advice,
        insights,
    )

    return CoachingSession(
        generated_at=(
            generated_at if generated_at is not None else datetime.now(timezone.utc)
        ),
        financial_health_score=float(
            snapshot.get(
                "health_score",
                0.0,
            )
        ),
        financial_health_status=str(
            snapshot.get(
                "health_status",
                "Unknown",
            )
        ),
        summary=summary,
        _advice=tuple(advice),
        _explanations=tuple(explanations),
        _insights=tuple(insights),
        _next_steps=tuple(next_steps),
        _warnings=tuple(warnings),
    )

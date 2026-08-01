from src.financial.engine.health_status import (
    HEALTH_SCORE_EXCELLENT_THRESHOLD,
    HEALTH_SCORE_FAIR_THRESHOLD,
)
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class HealthScoreRule(FinancialRule):
    """Evaluate financial health score."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation based on health score."""
        health_score = snapshot["health_score"]
        health_status = snapshot["health_status"]

        if health_score < HEALTH_SCORE_FAIR_THRESHOLD:
            return Recommendation(
                priority=RecommendationPriority.CRITICAL,
                category=RecommendationCategory.HEALTH,
                title="Financial Health Needs Attention",
                message=f"Your financial health status is {health_status}.",
                action="Review your cash flow, debt, savings, and budget priorities.",
            )

        if health_score >= HEALTH_SCORE_EXCELLENT_THRESHOLD:
            return Recommendation(
                priority=RecommendationPriority.LOW,
                category=RecommendationCategory.HEALTH,
                title="Strong Financial Health",
                message=f"Your financial health status is {health_status}.",
                action="Continue your current habits and consider long-term investing.",
            )

        return None

from collections import defaultdict

from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation


class RecommendationEngine:
    """Processes financial recommendations."""

    def prioritize(
        self,
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        """Sort recommendations by priority, highest first."""
        return sorted(
            recommendations,
            key=lambda recommendation: recommendation.priority,
            reverse=True,
        )

    def group_by_category(
        self,
        recommendations: list[Recommendation],
    ) -> dict[RecommendationCategory, list[Recommendation]]:
        """Group recommendations by category."""
        grouped: dict[RecommendationCategory, list[Recommendation]] = defaultdict(list)

        for recommendation in recommendations:
            grouped[recommendation.category].append(recommendation)

        return dict(grouped)

    def top_n(
        self,
        recommendations: list[Recommendation],
        limit: int,
    ) -> list[Recommendation]:
        """Return the top N recommendations by priority."""
        return self.prioritize(recommendations)[:limit]
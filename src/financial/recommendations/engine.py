from collections import defaultdict

from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.scoring import recommendation_score


class RecommendationEngine:
    """Processes financial recommendations."""

    def prioritize(
        self,
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        """Sort recommendations by recommendation score."""
        return sorted(
            recommendations,
            key=recommendation_score,
            reverse=True,
        )

    def group_by_category(
        self,
        recommendations: list[Recommendation],
    ) -> dict[
        RecommendationCategory,
        list[Recommendation],
    ]:
        grouped = defaultdict(list)

        for recommendation in recommendations:
            grouped[
                recommendation.category
            ].append(recommendation)

        return dict(grouped)

    def top_n(
        self,
        recommendations: list[Recommendation],
        limit: int,
    ) -> list[Recommendation]:
        if limit <= 0:
            return []

        return self.prioritize(
            recommendations
        )[:limit]

    def deduplicate(
        self,
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        """Remove duplicate recommendation titles."""
        unique = {}

        for recommendation in recommendations:
            unique.setdefault(
                recommendation.title,
                recommendation,
            )

        return list(unique.values())

    def process(
        self,
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        """
        Full recommendation pipeline.
        """
        recommendations = self.deduplicate(
            recommendations
        )

        return self.prioritize(
            recommendations
        )
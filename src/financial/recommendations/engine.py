from collections import defaultdict

from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.scoring import recommendation_score


class RecommendationEngine:
    """Processes and organizes financial recommendations."""

    def prioritize(
        self,
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        """Sort recommendations by intelligence score."""
        return sorted(
            recommendations,
            key=recommendation_score,
            reverse=True,
        )

    def group_by_category(
        self,
        recommendations: list[Recommendation],
    ) -> dict[RecommendationCategory, list[Recommendation]]:
        """Group recommendations by category."""
        grouped: dict[
            RecommendationCategory,
            list[Recommendation],
        ] = defaultdict(list)

        for recommendation in recommendations:
            grouped[recommendation.category].append(recommendation)

        return dict(grouped)

    def deduplicate(
        self,
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        """
        Remove duplicate recommendations.

        When duplicate keys exist, keep the recommendation with the
        highest intelligence score.
        """
        unique: dict[str, Recommendation] = {}

        for recommendation in recommendations:
            existing = unique.get(recommendation.key)

            if existing is None:
                unique[recommendation.key] = recommendation
                continue

            if (
                recommendation_score(recommendation)
                > recommendation_score(existing)
            ):
                unique[recommendation.key] = recommendation

        return list(unique.values())

    def top_n(
        self,
        recommendations: list[Recommendation],
        limit: int,
    ) -> list[Recommendation]:
        """Return the highest-ranked recommendations."""
        if limit <= 0:
            return []

        processed = self.process(recommendations)
        return processed[:limit]

    def process(
        self,
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        """Run the complete recommendation-processing pipeline."""
        unique_recommendations = self.deduplicate(recommendations)
        return self.prioritize(unique_recommendations)
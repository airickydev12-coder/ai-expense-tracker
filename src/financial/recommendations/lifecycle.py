from src.financial.recommendations.history import (
    RecommendationRecord,
)
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.status import (
    RecommendationStatus,
)


class RecommendationLifecycleManager:
    """Manages recommendation lifecycle records."""

    def __init__(self) -> None:
        self._records: dict[
            str,
            RecommendationRecord,
        ] = {}

    def get_records(
        self,
    ) -> list[RecommendationRecord]:
        """Return all lifecycle records."""
        return list(self._records.values())

    def get_record(
        self,
        recommendation_key: str,
    ) -> RecommendationRecord | None:
        """Return a lifecycle record by recommendation key."""
        normalized_key = recommendation_key.strip()

        return self._records.get(normalized_key)

    def replace_records(
        self,
        records: list[RecommendationRecord],
    ) -> None:
        """Replace all current records with loaded records."""
        self._records = {record.recommendation_key: record for record in records}

    def register(
        self,
        recommendation: Recommendation,
    ) -> RecommendationRecord:
        """Register a recommendation without creating duplicates."""
        existing_record = self.get_record(recommendation.key)

        if existing_record is not None:
            return existing_record

        record = RecommendationRecord.create(
            recommendation_key=recommendation.key,
            status=RecommendationStatus.NEW,
        )

        self._records[recommendation.key] = record

        return record

    def activate(
        self,
        recommendation_key: str,
        note: str = "",
    ) -> RecommendationRecord | None:
        """Mark a recommendation as active."""
        return self._set_status(
            recommendation_key,
            RecommendationStatus.ACTIVE,
            note,
        )

    def complete(
        self,
        recommendation_key: str,
        note: str = "",
    ) -> RecommendationRecord | None:
        """Mark a recommendation as completed."""
        return self._set_status(
            recommendation_key,
            RecommendationStatus.COMPLETED,
            note,
        )

    def dismiss(
        self,
        recommendation_key: str,
        note: str = "",
    ) -> RecommendationRecord | None:
        """Mark a recommendation as dismissed."""
        return self._set_status(
            recommendation_key,
            RecommendationStatus.DISMISSED,
            note,
        )

    def suppress(
        self,
        recommendation_key: str,
        note: str = "",
    ) -> RecommendationRecord | None:
        """Mark a recommendation as suppressed."""
        return self._set_status(
            recommendation_key,
            RecommendationStatus.SUPPRESSED,
            note,
        )

    def should_display(
        self,
        recommendation_key: str,
    ) -> bool:
        """Return whether a recommendation should be displayed."""
        record = self.get_record(recommendation_key)

        if record is None:
            return True

        return record.status in {
            RecommendationStatus.NEW,
            RecommendationStatus.ACTIVE,
        }

    def filter_displayable(
        self,
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        """Register and return recommendations eligible for display."""
        displayable: list[Recommendation] = []

        for recommendation in recommendations:
            record = self.register(recommendation)

            if record.status in {
                RecommendationStatus.NEW,
                RecommendationStatus.ACTIVE,
            }:
                displayable.append(recommendation)

        return displayable

    def clear(self) -> None:
        """Remove all lifecycle records."""
        self._records.clear()

    def _set_status(
        self,
        recommendation_key: str,
        status: RecommendationStatus,
        note: str,
    ) -> RecommendationRecord | None:
        """Update a lifecycle record status."""
        record = self.get_record(recommendation_key)

        if record is None:
            return None

        record.update_status(
            status=status,
            note=note,
        )

        return record

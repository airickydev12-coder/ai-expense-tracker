from dataclasses import dataclass

from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority


@dataclass
class Recommendation:
    """Represents a financial recommendation."""

    priority: RecommendationPriority | str
    category: RecommendationCategory | str
    title: str
    message: str
    action: str

    def __post_init__(self) -> None:
        """Normalize and validate recommendation fields."""
        if isinstance(self.priority, str):
            normalized_priority = (
                self.priority.strip()
                .upper()
                .replace(" ", "_")
            )

            try:
                self.priority = RecommendationPriority[normalized_priority]
            except KeyError as error:
                raise ValueError(
                    f"Invalid recommendation priority: {self.priority}"
                ) from error

        if isinstance(self.category, str):
            normalized_category = self.category.strip().lower()

            matching_category = next(
                (
                    category
                    for category in RecommendationCategory
                    if category.value.lower() == normalized_category
                    or category.name.lower() == normalized_category
                ),
                None,
            )

            if matching_category is None:
                raise ValueError(
                    f"Invalid recommendation category: {self.category}"
                )

            self.category = matching_category

        if not self.title.strip():
            raise ValueError("Recommendation title cannot be empty.")

        if not self.message.strip():
            raise ValueError("Recommendation message cannot be empty.")

        if not self.action.strip():
            raise ValueError("Recommendation action cannot be empty.")

    def to_dict(self) -> dict:
        """Convert the recommendation to a dictionary."""
        return {
            "priority": self.priority.name,
            "category": self.category.value,
            "score": self.score(),
            "title": self.title,
            "message": self.message,
            "action": self.action,
        }

    def score(self) -> int:
        """Return recommendation score."""
        return self.priority.value * 100
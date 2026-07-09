from dataclasses import dataclass

from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority


@dataclass
class Recommendation:
    """Represents a financial recommendation."""

    priority: RecommendationPriority
    category: RecommendationCategory
    title: str
    message: str
    action: str

    def to_dict(self) -> dict:
        """Convert recommendation to dictionary."""
        return {
            "priority": self.priority.name,
            "category": self.category.value,
            "title": self.title,
            "message": self.message,
            "action": self.action,
        }
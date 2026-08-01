from dataclasses import dataclass

from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority


@dataclass
class Recommendation:
    """Represents an actionable financial recommendation."""

    priority: RecommendationPriority
    category: RecommendationCategory
    title: str
    message: str
    action: str
    rationale: str = ""
    source_rule: str = ""

    def __post_init__(self) -> None:
        """Normalize recommendation fields."""

        if isinstance(self.priority, str):
            normalized = self.priority.upper().strip().replace(" ", "_")
            self.priority = RecommendationPriority[normalized]

        if isinstance(self.category, str):
            normalized = self.category.lower().strip()

            for category in RecommendationCategory:
                if (
                    category.name.lower() == normalized
                    or category.value.lower() == normalized
                ):
                    self.category = category
                    break

        self.title = self.title.strip()
        self.message = self.message.strip()
        self.action = self.action.strip()
        self.rationale = self.rationale.strip()
        self.source_rule = self.source_rule.strip()

    @property
    def key(self) -> str:
        """Stable identifier."""

        return (
            f"{self.category.name.lower()}:" f"{self.title.lower().replace(' ', '_')}"
        )

    @property
    def is_actionable(self) -> bool:
        """Whether user can take action."""

        return bool(self.action)

    def score(self) -> int:
        """Return recommendation score."""

        return self.priority.value * 100

    def to_dict(self) -> dict:
        """Serialize recommendation."""

        return {
            "key": self.key,
            "priority": self.priority.name,
            "category": self.category.value,
            "score": self.score(),
            "title": self.title,
            "message": self.message,
            "action": self.action,
            "rationale": self.rationale,
            "source_rule": self.source_rule,
            "is_actionable": self.is_actionable,
        }

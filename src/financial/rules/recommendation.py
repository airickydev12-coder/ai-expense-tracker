from dataclasses import dataclass


@dataclass
class Recommendation:
    """Represents a financial recommendation."""

    priority: str
    category: str
    title: str
    message: str
    action: str

    def to_dict(self) -> dict:
        """Convert recommendation to dictionary."""
        return {
            "priority": self.priority,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "action": self.action,
        }
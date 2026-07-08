from abc import ABC, abstractmethod

from src.financial.rules.recommendation import Recommendation


class FinancialRule(ABC):
    """Base class for all financial rules."""

    @abstractmethod
    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation or None."""
        raise NotImplementedError
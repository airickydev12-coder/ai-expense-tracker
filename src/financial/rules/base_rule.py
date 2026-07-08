from abc import ABC, abstractmethod


class FinancialRule(ABC):
    """Base class for all financial rules."""

    @abstractmethod
    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation or None."""
        raise NotImplementedError
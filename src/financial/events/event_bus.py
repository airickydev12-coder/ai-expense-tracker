from collections import defaultdict
from collections.abc import Callable

from src.financial.events.event_types import FinancialEvent


class EventBus:
    """Simple publish/subscribe event bus."""

    def __init__(self) -> None:
        self._handlers: dict[FinancialEvent, list[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event: FinancialEvent, handler: Callable[..., None]) -> None:
        self._handlers[event].append(handler)

    def publish(self, event: FinancialEvent, *args, **kwargs) -> None:
        for handler in self._handlers[event]:
            handler(*args, **kwargs)
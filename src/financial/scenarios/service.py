from collections.abc import Callable
from typing import Any

from src.core.exceptions import NotFoundError, ValidationError
from src.financial.scenarios.models import (
    ScenarioRequest,
    ScenarioResult,
    ScenarioType,
)


ScenarioHandler = Callable[
    [dict, dict[str, Any]],
    ScenarioResult,
]


class ScenarioService:
    """Registers and executes financial scenarios."""

    def __init__(self) -> None:
        self._handlers: dict[
            ScenarioType,
            ScenarioHandler,
        ] = {}

    def register_handler(
        self,
        scenario_type: ScenarioType,
        handler: ScenarioHandler,
    ) -> None:
        """Register a handler for a scenario type."""
        self._handlers[scenario_type] = handler

    def has_handler(
        self,
        scenario_type: ScenarioType,
    ) -> bool:
        """Return whether a scenario handler is registered."""
        return scenario_type in self._handlers

    def get_registered_types(
        self,
    ) -> list[ScenarioType]:
        """Return all registered scenario types."""
        return list(self._handlers)

    def run(
        self,
        request: ScenarioRequest,
        snapshot: dict,
    ) -> ScenarioResult:
        """Execute a scenario against a financial snapshot."""
        self._validate_snapshot(snapshot)

        handler = self._handlers.get(request.scenario_type)

        if handler is None:
            raise NotFoundError(
                "No handler is registered for scenario type: "
                f"{request.scenario_type.value}"
            )

        scenario_snapshot = snapshot.copy()
        scenario_parameters = request.parameters.copy()

        result = handler(
            scenario_snapshot,
            scenario_parameters,
        )

        if result.scenario_type != request.scenario_type:
            raise ValidationError(
                "Scenario handler returned an unexpected " "scenario type."
            )

        return result

    def clear_handlers(self) -> None:
        """Remove all registered scenario handlers."""
        self._handlers.clear()

    @staticmethod
    def _validate_snapshot(
        snapshot: dict,
    ) -> None:
        """Validate the minimum snapshot fields."""
        required_fields = {
            "total_income",
            "total_expenses",
            "net_cash_flow",
            "total_account_balance",
            "total_goal_progress",
            "total_debt",
            "net_worth",
            "health_score",
            "health_status",
        }

        missing_fields = required_fields - snapshot.keys()

        if missing_fields:
            formatted_fields = ", ".join(sorted(missing_fields))

            raise ValidationError(
                "Financial snapshot is missing required " f"fields: {formatted_fields}"
            )


scenario_service = ScenarioService()


def register_scenario_handler(
    scenario_type: ScenarioType,
    handler: ScenarioHandler,
) -> None:
    """Register a handler with the shared service."""
    scenario_service.register_handler(
        scenario_type,
        handler,
    )


def run_financial_scenario(
    request: ScenarioRequest,
    snapshot: dict,
) -> ScenarioResult:
    """Run a scenario using the shared service."""
    return scenario_service.run(
        request=request,
        snapshot=snapshot,
    )


def reset_scenario_handlers() -> None:
    """Clear handlers from the shared service."""
    scenario_service.clear_handlers()

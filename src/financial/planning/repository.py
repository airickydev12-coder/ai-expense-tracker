"""SQLite persistence for financial-goal planning requests."""

import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError, ValidationError
from src.core.logging import get_logger
from src.core.money import CURRENCY_PRECISION
from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    MoneyInput,
    to_money,
)
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal

logger = get_logger(__name__)


def load_goal_planning_requests_from_file(
    goals: Sequence[Goal],
    file_path: Path = DB_PATH,
) -> dict[int, GoalPlanningRequest]:
    """Load requests and bind them to the current Goal objects."""
    try:
        with get_connection(file_path) as connection:
            rows = connection.execute("""
                SELECT goal_id, target_date, planned_monthly_contribution, priority
                FROM goal_planning_requests
                """).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load goal planning requests from {file_path}"
        ) from error

    goals_by_id = {goal.id: goal for goal in goals}
    requests: dict[int, GoalPlanningRequest] = {}

    for row in rows:
        request = _request_from_record(
            dict(row),
            goals_by_id=goals_by_id,
        )

        if request is None:
            continue

        requests[request.goal.id] = request

    logger.debug(
        "Loaded %d goal planning request(s) from %s",
        len(requests),
        file_path,
    )

    return requests


def save_goal_planning_requests_to_file(
    requests: Mapping[int, GoalPlanningRequest],
    file_path: Path = DB_PATH,
) -> None:
    """Save goal-planning requests, replacing all existing rows."""
    _validate_request_mapping(requests)

    records = [_request_to_record(request) for request in requests.values()]

    try:
        with get_connection(file_path) as connection:
            connection.execute("DELETE FROM goal_planning_requests")
            connection.executemany(
                """
                INSERT INTO goal_planning_requests (
                    goal_id, target_date, planned_monthly_contribution, priority
                )
                VALUES (
                    :goal_id, :target_date, :planned_monthly_contribution, :priority
                )
                """,
                records,
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to save goal planning requests to {file_path}"
        ) from error

    logger.debug(
        "Saved %d goal planning request(s) to %s",
        len(records),
        file_path,
    )


def remove_goal_planning_request_from_file(
    goal_id: int,
    file_path: Path = DB_PATH,
) -> bool:
    """Remove one persisted request by goal ID."""
    if goal_id <= 0:
        raise ValidationError("Goal ID must be greater than zero.")

    try:
        with get_connection(file_path) as connection:
            cursor = connection.execute(
                "DELETE FROM goal_planning_requests WHERE goal_id = ?",
                (goal_id,),
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to remove goal planning request from {file_path}"
        ) from error

    removed = cursor.rowcount > 0

    if removed:
        logger.debug(
            "Removed goal planning request for goal %d from %s",
            goal_id,
            file_path,
        )

    return removed


def _request_to_record(
    request: GoalPlanningRequest,
) -> dict[str, Any]:
    """Convert one planning request into a row-ready record."""
    return {
        "goal_id": request.goal.id,
        "target_date": request.target_date.isoformat(),
        "planned_monthly_contribution": (
            _money_to_json(request.planned_monthly_contribution)
        ),
        "priority": request.priority.name,
    }


def _request_from_record(
    record: Mapping[str, Any],
    *,
    goals_by_id: Mapping[int, Goal],
) -> GoalPlanningRequest | None:
    """Convert one persisted row into a planning request."""
    try:
        goal_id = _parse_goal_id(record)
        target_date_value = date.fromisoformat(str(record["target_date"]))
        contribution = _money_from_json(record["planned_monthly_contribution"])
        priority = GoalPriority[str(record["priority"])]
    except KeyError as error:
        raise PersistenceError(
            f"Goal-planning request record is missing field {error.args[0]!r}."
        ) from error
    except (TypeError, ValueError, InvalidOperation) as error:
        raise PersistenceError(
            "Goal-planning request record contains invalid values."
        ) from error

    goal = goals_by_id.get(goal_id)

    if goal is None:
        return None

    return GoalPlanningRequest(
        goal=goal,
        target_date=target_date_value,
        planned_monthly_contribution=contribution,
        priority=priority,
    )


def _money_to_json(value: MoneyInput) -> str:
    """Convert a monetary value to a fixed-precision string."""
    amount = to_money(value)

    if not amount.is_finite():
        raise PersistenceError("Goal-planning monetary values must be finite.")

    return format(
        amount.quantize(CURRENCY_PRECISION),
        ".2f",
    )


def _money_from_json(value: object) -> Decimal:
    """Convert a persisted monetary value into a Decimal."""
    if isinstance(value, bool):
        raise TypeError("Boolean values are not valid monetary values.")

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise PersistenceError("Invalid persisted monetary value.") from error

    if not amount.is_finite():
        raise PersistenceError("Persisted monetary values must be finite.")

    return amount.quantize(CURRENCY_PRECISION)


def _parse_goal_id(
    record: Mapping[str, Any],
) -> int:
    """Parse and validate a persisted goal ID."""
    try:
        goal_id = int(record["goal_id"])
    except (KeyError, TypeError, ValueError) as error:
        raise PersistenceError(
            "Goal-planning request record contains an invalid goal_id."
        ) from error

    if goal_id <= 0:
        raise PersistenceError(
            "Goal-planning request goal_id must be greater than zero."
        )

    return goal_id


def _validate_request_mapping(
    requests: Mapping[int, GoalPlanningRequest],
) -> None:
    """Validate the mapping supplied to the persistence layer."""
    for goal_id, request in requests.items():
        if not isinstance(goal_id, int):
            raise TypeError("Goal-planning request keys must be integers.")

        if not isinstance(request, GoalPlanningRequest):
            raise TypeError(
                "Every saved planning request must be a GoalPlanningRequest instance."
            )

        if request.goal.id != goal_id:
            raise PersistenceError("Goal-planning request key must match its goal ID.")

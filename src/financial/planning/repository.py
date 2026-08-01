"""JSON persistence for financial-goal planning requests."""

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.core.config import GOAL_PLANNING_REQUESTS_FILE
from src.core.exceptions import PersistenceError, ValidationError
from src.core.logging import get_logger
from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    MoneyInput,
    to_money,
)
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal

logger = get_logger(__name__)

MONEY_QUANTUM = Decimal("0.01")


def load_goal_planning_requests_from_file(
    goals: Sequence[Goal],
    file_path: Path = GOAL_PLANNING_REQUESTS_FILE,
) -> dict[int, GoalPlanningRequest]:
    """Load requests and bind them to the current Goal objects."""
    if not file_path.exists():
        return {}

    try:
        with file_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        raise PersistenceError(
            f"Goal-planning request file contains invalid JSON: {file_path}"
        ) from error
    except OSError as error:
        raise PersistenceError(
            f"Unable to read goal-planning request file: {file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Goal-planning requests must be stored as a JSON list.")

    goals_by_id = {goal.id: goal for goal in goals}
    requests: dict[int, GoalPlanningRequest] = {}

    for index, record in enumerate(raw_data, start=1):
        request = _request_from_record(
            record,
            goals_by_id=goals_by_id,
            record_number=index,
        )

        if request is None:
            continue

        if request.goal.id in requests:
            raise PersistenceError(
                "Goal-planning request file contains duplicate goal ID "
                f"{request.goal.id}."
            )

        requests[request.goal.id] = request

    logger.debug(
        "Loaded %d goal planning request(s) from %s",
        len(requests),
        file_path,
    )

    return requests


def save_goal_planning_requests_to_file(
    requests: Mapping[int, GoalPlanningRequest],
    file_path: Path = GOAL_PLANNING_REQUESTS_FILE,
) -> None:
    """Save goal-planning requests as JSON using an atomic replacement."""
    _validate_request_mapping(requests)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    records = [
        _request_to_record(request)
        for _, request in sorted(
            requests.items(),
            key=lambda item: item[0],
        )
    ]

    temporary_path = file_path.with_suffix(file_path.suffix + ".tmp")

    try:
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                records,
                file,
                indent=4,
            )
            file.write("\n")

        temporary_path.replace(file_path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise

    logger.debug(
        "Saved %d goal planning request(s) to %s",
        len(records),
        file_path,
    )


def remove_goal_planning_request_from_file(
    goal_id: int,
    file_path: Path = GOAL_PLANNING_REQUESTS_FILE,
) -> bool:
    """Remove one persisted request by goal ID."""
    if goal_id <= 0:
        raise ValidationError("Goal ID must be greater than zero.")

    if not file_path.exists():
        return False

    try:
        with file_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        raise PersistenceError(
            f"Goal-planning request file contains invalid JSON: {file_path}"
        ) from error
    except OSError as error:
        raise PersistenceError(
            f"Unable to read goal-planning request file: {file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Goal-planning requests must be stored as a JSON list.")

    retained_records: list[dict[str, Any]] = []
    removed = False

    for record in raw_data:
        if not isinstance(record, dict):
            raise PersistenceError(
                "Every goal-planning request record must be a JSON object."
            )

        record_goal_id = _parse_goal_id(record)

        if record_goal_id == goal_id:
            removed = True
            continue

        retained_records.append(record)

    if not removed:
        return False

    temporary_path = file_path.with_suffix(file_path.suffix + ".tmp")

    try:
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                retained_records,
                file,
                indent=4,
            )
            file.write("\n")

        temporary_path.replace(file_path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise

    logger.debug(
        "Removed goal planning request for goal %d from %s",
        goal_id,
        file_path,
    )

    return True


def _request_to_record(
    request: GoalPlanningRequest,
) -> dict[str, Any]:
    """Convert one planning request into a JSON-safe record."""
    return {
        "goal_id": request.goal.id,
        "target_date": request.target_date.isoformat(),
        "planned_monthly_contribution": (
            _money_to_json(request.planned_monthly_contribution)
        ),
        "priority": request.priority.name,
    }


def _request_from_record(
    record: object,
    *,
    goals_by_id: Mapping[int, Goal],
    record_number: int,
) -> GoalPlanningRequest | None:
    """Convert one persisted record into a planning request."""
    if not isinstance(record, dict):
        raise PersistenceError(
            f"Goal-planning request record {record_number} " "must be a JSON object."
        )

    try:
        goal_id = _parse_goal_id(record)
        target_date = date.fromisoformat(str(record["target_date"]))
        contribution = _money_from_json(record["planned_monthly_contribution"])
        priority = GoalPriority[str(record["priority"])]
    except KeyError as error:
        raise PersistenceError(
            f"Goal-planning request record {record_number} "
            f"is missing field {error.args[0]!r}."
        ) from error
    except (TypeError, ValueError, InvalidOperation) as error:
        raise PersistenceError(
            f"Goal-planning request record {record_number} " "contains invalid values."
        ) from error

    goal = goals_by_id.get(goal_id)

    if goal is None:
        return None

    return GoalPlanningRequest(
        goal=goal,
        target_date=target_date,
        planned_monthly_contribution=contribution,
        priority=priority,
    )


def _money_to_json(value: MoneyInput) -> str:
    """Convert a monetary value to a fixed-precision JSON string."""
    amount = to_money(value)

    if not amount.is_finite():
        raise PersistenceError("Goal-planning monetary values must be finite.")

    return format(
        amount.quantize(MONEY_QUANTUM),
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

    return amount.quantize(MONEY_QUANTUM)


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
        raise PersistenceError("Goal-planning request goal_id must be greater than zero.")

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
                "Every saved planning request must be a "
                "GoalPlanningRequest instance."
            )

        if request.goal.id != goal_id:
            raise PersistenceError("Goal-planning request key must match its goal ID.")

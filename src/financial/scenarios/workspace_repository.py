import json
import sqlite3
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.scenarios.models import (
    ScenarioAssumption,
    ScenarioImpact,
    ScenarioResult,
    ScenarioType,
)

logger = get_logger(__name__)


class _DecimalEncoder(json.JSONEncoder):
    """
    Serialize Decimal values found anywhere in a scenario result.

    original_snapshot/projected_snapshot are free-form dicts that can
    contain Decimal values at any depth (top-level totals, nested
    accounts/goals/debts/bills). A tagged object lets the matching
    object_hook restore Decimal on load without needing to know which
    keys are monetary.
    """

    def default(self, o: object) -> Any:
        if isinstance(o, Decimal):
            return {"__decimal__": str(o)}

        return super().default(o)


def _decimal_object_hook(data: dict) -> object:
    """Restore Decimal values tagged by _DecimalEncoder."""
    if set(data.keys()) == {"__decimal__"}:
        return Decimal(data["__decimal__"])

    return data


def _scenario_type_from_value(
    value: str,
) -> ScenarioType:
    """Convert a stored scenario type into an enum value."""
    try:
        return ScenarioType[value]
    except KeyError:
        pass

    for scenario_type in ScenarioType:
        if scenario_type.value == value:
            return scenario_type

    raise PersistenceError(f"Unknown scenario type: {value}")


def _assumption_from_dict(
    data: dict,
) -> ScenarioAssumption:
    """Create a scenario assumption from stored data."""
    if not isinstance(data, dict):
        raise PersistenceError("Scenario assumption must be a JSON object.")

    return ScenarioAssumption(
        name=str(data["name"]),
        value=data["value"],
        description=str(
            data.get(
                "description",
                "",
            )
        ),
    )


def _impact_from_dict(
    data: dict,
) -> ScenarioImpact:
    """Create a scenario impact from stored data."""
    if not isinstance(data, dict):
        raise PersistenceError("Scenario impact must be a JSON object.")

    return ScenarioImpact(
        metric=str(data["metric"]),
        original_value=Decimal(str(data["original_value"])),
        projected_value=Decimal(str(data["projected_value"])),
        change=Decimal(str(data["change"])),
    )


def _result_from_dict(
    data: dict,
) -> ScenarioResult:
    """Create a scenario result from stored data."""
    if not isinstance(data, dict):
        raise PersistenceError("Scenario result must be a JSON object.")

    scenario_type = _scenario_type_from_value(str(data["scenario_type"]))

    assumptions_data = data.get(
        "assumptions",
        [],
    )
    impacts_data = data.get(
        "impacts",
        [],
    )

    if not isinstance(
        assumptions_data,
        list,
    ):
        raise PersistenceError("Scenario assumptions must be a JSON list.")

    if not isinstance(
        impacts_data,
        list,
    ):
        raise PersistenceError("Scenario impacts must be a JSON list.")

    original_snapshot = data.get(
        "original_snapshot",
        {},
    )
    projected_snapshot = data.get(
        "projected_snapshot",
        {},
    )

    if not isinstance(
        original_snapshot,
        dict,
    ):
        raise PersistenceError("Original snapshot must be a JSON object.")

    if not isinstance(
        projected_snapshot,
        dict,
    ):
        raise PersistenceError("Projected snapshot must be a JSON object.")

    benefits = data.get(
        "benefits",
        [],
    )
    risks = data.get(
        "risks",
        [],
    )
    recommendations = data.get(
        "recommendations",
        [],
    )

    if not isinstance(benefits, list):
        raise PersistenceError("Scenario benefits must be a JSON list.")

    if not isinstance(risks, list):
        raise PersistenceError("Scenario risks must be a JSON list.")

    if not isinstance(
        recommendations,
        list,
    ):
        raise PersistenceError("Scenario recommendations must be a JSON list.")

    return ScenarioResult(
        scenario_type=scenario_type,
        name=str(data["name"]),
        description=str(
            data.get(
                "description",
                "",
            )
        ),
        assumptions=[_assumption_from_dict(item) for item in assumptions_data],
        original_snapshot=original_snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[_impact_from_dict(item) for item in impacts_data],
        benefits=[str(item) for item in benefits],
        risks=[str(item) for item in risks],
        recommendations=[str(item) for item in recommendations],
    )


def load_workspace_from_file(
    file_path: Path = DB_PATH,
) -> list[ScenarioResult]:
    """Load saved scenario results from the database."""
    try:
        with get_connection(file_path) as connection:
            rows = connection.execute(
                "SELECT data FROM scenario_workspace ORDER BY name"
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load scenario workspace from {file_path}"
        ) from error

    try:
        results = [
            _result_from_dict(json.loads(row["data"], object_hook=_decimal_object_hook))
            for row in rows
        ]
    except json.JSONDecodeError as error:
        raise PersistenceError("Scenario workspace contains invalid JSON.") from error

    logger.debug(
        "Loaded %d scenario result(s) from %s",
        len(results),
        file_path,
    )

    return results


def save_workspace_to_file(
    results: list[ScenarioResult],
    file_path: Path = DB_PATH,
) -> None:
    """Save scenario results to the database, replacing all existing rows."""
    records = [
        {
            "name": result.name,
            "data": json.dumps(result.to_dict(), cls=_DecimalEncoder),
        }
        for result in results
    ]

    try:
        with get_connection(file_path) as connection:
            connection.execute("DELETE FROM scenario_workspace")
            connection.executemany(
                "INSERT INTO scenario_workspace (name, data) VALUES (:name, :data)",
                records,
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to save scenario workspace to {file_path}"
        ) from error

    logger.debug(
        "Saved %d scenario result(s) to %s",
        len(results),
        file_path,
    )


def clear_workspace_file(
    file_path: Path = DB_PATH,
) -> None:
    """Remove all persisted scenario workspace results."""
    try:
        with get_connection(file_path) as connection:
            connection.execute("DELETE FROM scenario_workspace")
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to clear scenario workspace at {file_path}"
        ) from error

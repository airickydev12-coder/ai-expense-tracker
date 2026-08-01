import json
from decimal import Decimal

import pytest

from src.core.db import get_connection
from src.financial.scenarios.models import (
    ScenarioAssumption,
    ScenarioImpact,
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.workspace_repository import (
    clear_workspace_file,
    load_workspace_from_file,
    save_workspace_to_file,
)


def build_snapshot() -> dict:
    """Create a reusable scenario snapshot."""
    return {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 8000,
        "total_goal_progress": 2500,
        "total_debt": 10000,
        "net_worth": 500,
        "health_score": 70,
        "health_status": "Good",
    }


def build_result() -> ScenarioResult:
    """Create a complete scenario result."""
    original_snapshot = build_snapshot()

    projected_snapshot = {
        **original_snapshot,
        "net_worth": 6500,
        "net_cash_flow": 2500,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Income Increase",
        description="Model a ten percent raise.",
        assumptions=[
            ScenarioAssumption(
                name="Increase Percentage",
                value=10,
                description="Projected raise.",
            )
        ],
        original_snapshot=original_snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[
            ScenarioImpact.create(
                metric="Net Worth",
                original_value=500,
                projected_value=6500,
            )
        ],
        benefits=[
            "Increase available income.",
        ],
        risks=[
            "The increase may not be guaranteed.",
        ],
        recommendations=[
            "Save part of the additional income.",
        ],
    )


def test_save_and_load_workspace(
    db_path,
):
    original_results = [build_result()]

    save_workspace_to_file(
        original_results,
        db_path,
    )

    loaded_results = load_workspace_from_file(db_path)

    assert loaded_results == original_results


def test_save_and_load_workspace_with_decimal_snapshot(
    db_path,
):
    """Snapshots built from live domain models contain Decimal values.

    json.dumps cannot serialize Decimal natively, so this guards against
    a regression where saving a real (non-test-literal) scenario result
    raised TypeError: Object of type Decimal is not JSON serializable.
    """
    snapshot = {
        "total_income": Decimal("5000.00"),
        "total_expenses": Decimal("3000.00"),
        "net_cash_flow": Decimal("2000.00"),
        "total_account_balance": Decimal("8000.00"),
        "total_goal_progress": Decimal("2500.00"),
        "total_debt": Decimal("10000.00"),
        "net_worth": Decimal("500.00"),
        "health_score": 70,
        "health_status": "Good",
        "accounts": [
            {
                "id": 1,
                "name": "Checking",
                "balance": Decimal("1234.56"),
            }
        ],
    }

    result = ScenarioResult(
        scenario_type=ScenarioType.INCOME_INCREASE,
        name="Income Increase",
        description="Model a ten percent raise.",
        assumptions=[],
        original_snapshot=snapshot,
        projected_snapshot=snapshot,
        impacts=[
            ScenarioImpact.create(
                metric="Net Worth",
                original_value=Decimal("500.00"),
                projected_value=Decimal("6500.00"),
            )
        ],
    )

    save_workspace_to_file(
        [result],
        db_path,
    )

    loaded_results = load_workspace_from_file(db_path)

    loaded_snapshot = loaded_results[0].original_snapshot

    assert loaded_snapshot["total_account_balance"] == Decimal("8000.00")
    assert isinstance(
        loaded_snapshot["total_account_balance"],
        Decimal,
    )
    assert loaded_snapshot["accounts"][0]["balance"] == Decimal("1234.56")
    assert isinstance(
        loaded_snapshot["accounts"][0]["balance"],
        Decimal,
    )


def test_load_workspace_returns_empty_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_workspace.db"

    assert load_workspace_from_file(db_path) == []


def test_save_workspace_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "scenario_workspace.db"

    save_workspace_to_file(
        [build_result()],
        db_path,
    )

    assert db_path.exists()


def test_load_workspace_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "scenario_workspace.db"

    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load scenario workspace",
    ):
        load_workspace_from_file(db_path)


def test_load_workspace_rejects_unknown_scenario_type(
    db_path,
):
    data = build_result().to_dict()
    data["scenario_type"] = "UNKNOWN_SCENARIO"

    with get_connection(db_path) as connection:
        connection.execute(
            "INSERT INTO scenario_workspace (name, data) VALUES (:name, :data)",
            {
                "name": data["name"],
                "data": json.dumps(data),
            },
        )

    with pytest.raises(
        ValueError,
        match="Unknown scenario type",
    ):
        load_workspace_from_file(db_path)


def test_clear_workspace_file(
    db_path,
):
    save_workspace_to_file(
        [build_result()],
        db_path,
    )

    assert load_workspace_from_file(db_path) != []

    clear_workspace_file(db_path)

    assert load_workspace_from_file(db_path) == []


def test_clear_workspace_with_no_rows_is_safe(
    tmp_path,
):
    db_path = tmp_path / "missing_workspace.db"

    clear_workspace_file(db_path)

    assert load_workspace_from_file(db_path) == []

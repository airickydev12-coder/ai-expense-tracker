from src.financial.scenarios.models import (
    ScenarioImpact,
    ScenarioResult,
    ScenarioType,
)
from src.presentation import scenario_cli


def build_snapshot() -> dict:
    """Create a snapshot for scenario CLI tests."""
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
        "category_totals": {
            "Food": 600,
        },
        "debts": [
            {
                "id": 1,
                "name": "Credit Card",
                "balance": 10000,
                "interest_rate": 18,
                "minimum_payment": 300,
            }
        ],
    }


def build_result() -> ScenarioResult:
    """Create a scenario result for CLI tests."""
    snapshot = build_snapshot()

    return ScenarioResult(
        scenario_type=ScenarioType.EXPENSE_REDUCTION,
        name="Food Expense Reduction",
        description="Reduce food expenses.",
        assumptions=[],
        original_snapshot=snapshot,
        projected_snapshot={
            **snapshot,
            "total_expenses": 2880,
        },
        impacts=[
            ScenarioImpact.create(
                metric="Total Expenses",
                original_value=3000,
                projected_value=2880,
            )
        ],
    )


def test_select_expense_category(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    result = scenario_cli.select_expense_category(build_snapshot())

    assert result == "Food"


def test_select_debt_id(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    result = scenario_cli.select_debt_id(build_snapshot())

    assert result == 1


def test_run_expense_reduction_flow(
    monkeypatch,
):
    captured: dict = {}

    inputs = iter(
        [
            "1",
            "20",
            "12",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    def fake_run(
        request,
        snapshot,
    ):
        captured["request"] = request
        captured["snapshot"] = snapshot
        return build_result()

    monkeypatch.setattr(
        scenario_cli,
        "run_financial_scenario",
        fake_run,
    )

    monkeypatch.setattr(
        scenario_cli,
        "save_result_to_workspace",
        lambda result: captured.update(
            {
                "saved_result": result,
            }
        ),
    )

    monkeypatch.setattr(
        scenario_cli,
        "display_scenario_result",
        lambda result: captured.update(
            {
                "result": result,
            }
        ),
    )

    scenario_cli.run_expense_reduction_flow(build_snapshot())

    assert captured["request"].scenario_type == ScenarioType.EXPENSE_REDUCTION
    assert captured["request"].parameters["reduction_percentage"] == 20
    assert captured["result"].name == ("Food Expense Reduction")
    assert captured["saved_result"] == captured["result"]


def test_manage_scenarios_routes_income(
    monkeypatch,
):
    captured = {
        "called": False,
    }

    choices = iter(
        [
            "2",
            "6",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(choices),
    )

    monkeypatch.setattr(
        scenario_cli,
        "display_scenario_management_menu",
        lambda: None,
    )

    monkeypatch.setattr(
        scenario_cli,
        "build_current_financial_snapshot",
        build_snapshot,
    )

    def fake_income_flow(snapshot):
        captured["called"] = True

    monkeypatch.setattr(
        scenario_cli,
        "run_income_increase_flow",
        fake_income_flow,
    )

    scenario_cli.manage_scenarios()

    assert captured["called"] is True


def test_manage_scenarios_routes_workspace(
    monkeypatch,
):
    captured = {
        "called": False,
    }

    choices = iter(
        [
            "5",
            "6",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(choices),
    )

    monkeypatch.setattr(
        scenario_cli,
        "display_scenario_management_menu",
        lambda: None,
    )

    def fake_manage_workspace():
        captured["called"] = True

    monkeypatch.setattr(
        scenario_cli,
        "manage_scenario_workspace",
        fake_manage_workspace,
    )

    scenario_cli.manage_scenarios()

    assert captured["called"] is True


def test_execute_scenario_handles_error(
    monkeypatch,
    capsys,
):
    captured = {
        "saved": False,
        "displayed": False,
    }

    def fake_run(
        request,
        snapshot,
    ):
        raise ValueError("Invalid scenario.")

    monkeypatch.setattr(
        scenario_cli,
        "run_financial_scenario",
        fake_run,
    )

    monkeypatch.setattr(
        scenario_cli,
        "save_result_to_workspace",
        lambda result: captured.update(
            {
                "saved": True,
            }
        ),
    )

    monkeypatch.setattr(
        scenario_cli,
        "display_scenario_result",
        lambda result: captured.update(
            {
                "displayed": True,
            }
        ),
    )

    request = scenario_cli.ScenarioRequest(
        scenario_type=ScenarioType.INCOME_INCREASE,
        name="Income Increase",
        description="",
        parameters={
            "increase_percentage": 10,
        },
    )

    scenario_cli._execute_scenario(
        request,
        build_snapshot(),
    )

    output = capsys.readouterr().out

    assert "Unable to run scenario" in output
    assert "Invalid scenario" in output
    assert captured["saved"] is False
    assert captured["displayed"] is False


def test_execute_scenario_persists_and_displays_result(
    monkeypatch,
    capsys,
):
    captured: dict = {}
    expected_result = build_result()

    monkeypatch.setattr(
        scenario_cli,
        "run_financial_scenario",
        lambda request, snapshot: expected_result,
    )

    monkeypatch.setattr(
        scenario_cli,
        "save_result_to_workspace",
        lambda result: captured.update(
            {
                "saved_result": result,
            }
        ),
    )

    monkeypatch.setattr(
        scenario_cli,
        "display_scenario_result",
        lambda result: captured.update(
            {
                "displayed_result": result,
            }
        ),
    )

    request = scenario_cli.ScenarioRequest(
        scenario_type=ScenarioType.EXPENSE_REDUCTION,
        name="Food Expense Reduction",
        description="",
        parameters={
            "category": "Food",
            "reduction_percentage": 20,
        },
    )

    scenario_cli._execute_scenario(
        request,
        build_snapshot(),
    )

    output = capsys.readouterr().out

    assert captured["saved_result"] == expected_result
    assert captured["displayed_result"] == expected_result
    assert "Scenario saved to the current planning workspace." in output

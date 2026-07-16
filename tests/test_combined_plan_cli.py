from src.financial.scenarios.models import (
    ScenarioRequest,
    ScenarioType,
)
from src.financial.scenarios.plan import (
    ScenarioPlanResult,
    build_cumulative_scenario_report,
)
from src.presentation import combined_plan_cli


def build_snapshot() -> dict:
    """Create a snapshot for combined-plan CLI tests."""
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


def build_request() -> ScenarioRequest:
    """Create a combined-plan request."""
    return ScenarioRequest(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Income Increase",
        description="",
        parameters={
            "increase_percentage": 10,
            "horizon_months": 12,
        },
    )


def build_plan() -> ScenarioPlanResult:
    """Create a completed combined plan."""
    original = build_snapshot()

    projected = {
        **original,
        "total_income": 5500,
        "net_cash_flow": 2500,
        "net_worth": 6500,
    }

    return ScenarioPlanResult(
        name="Growth Plan",
        description="Increase income.",
        original_snapshot=original,
        projected_snapshot=projected,
        steps=[],
        cumulative_report=(
            build_cumulative_scenario_report(
                original,
                projected,
            )
        ),
    )


def test_select_expense_category(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    result = combined_plan_cli.select_expense_category(build_snapshot())

    assert result == "Food"


def test_select_debt_id(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    result = combined_plan_cli.select_debt_id(build_snapshot())

    assert result == 1


def test_build_income_increase_request(
    monkeypatch,
):
    inputs = iter(
        [
            "10",
            "12",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    request = combined_plan_cli.build_income_increase_request()

    assert request is not None
    assert request.scenario_type == ScenarioType.INCOME_INCREASE
    assert request.parameters["increase_percentage"] == 10
    assert request.parameters["horizon_months"] == 12


def test_remove_plan_step(
    monkeypatch,
):
    requests = [
        build_request(),
    ]

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    monkeypatch.setattr(
        combined_plan_cli,
        "display_combined_plan_steps",
        lambda requests: None,
    )

    combined_plan_cli.remove_plan_step(requests)

    assert requests == []


def test_run_combined_plan_builder(
    monkeypatch,
):
    captured: dict = {}

    inputs = iter(
        [
            "Growth Plan",
            "Increase income.",
            "2",
            "10",
            "12",
            "7",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        combined_plan_cli,
        "build_current_financial_snapshot",
        build_snapshot,
    )

    monkeypatch.setattr(
        combined_plan_cli,
        "display_combined_plan_builder_menu",
        lambda requests: None,
    )

    def fake_run_plan(
        *,
        name,
        description,
        requests,
        snapshot,
    ):
        captured["name"] = name
        captured["description"] = description
        captured["requests"] = requests
        captured["snapshot"] = snapshot
        return build_plan()

    monkeypatch.setattr(
        combined_plan_cli,
        "run_combined_scenario_plan",
        fake_run_plan,
    )

    monkeypatch.setattr(
        combined_plan_cli,
        "display_combined_plan_result",
        lambda plan: captured.update(
            {
                "plan": plan,
            }
        ),
    )

    combined_plan_cli.run_combined_plan_builder()

    assert captured["name"] == "Growth Plan"
    assert captured["description"] == ("Increase income.")
    assert len(captured["requests"]) == 1
    assert captured["requests"][0].scenario_type == ScenarioType.INCOME_INCREASE
    assert captured["plan"].name == "Growth Plan"


def test_builder_requires_at_least_one_step(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "Empty Plan",
            "",
            "7",
            "8",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        combined_plan_cli,
        "build_current_financial_snapshot",
        build_snapshot,
    )

    monkeypatch.setattr(
        combined_plan_cli,
        "display_combined_plan_builder_menu",
        lambda requests: None,
    )

    combined_plan_cli.run_combined_plan_builder()

    output = capsys.readouterr().out

    assert "Add at least one scenario step" in output
    assert "Combined plan was cancelled." in output


def test_builder_rejects_empty_name(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    combined_plan_cli.run_combined_plan_builder()

    output = capsys.readouterr().out

    assert "Combined plan name cannot be empty." in output

import pytest

from src.financial.scenarios.models import (
    ScenarioAssumption,
    ScenarioImpact,
    ScenarioRequest,
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.service import (
    ScenarioService,
    register_scenario_handler,
    reset_scenario_handlers,
    run_financial_scenario,
    scenario_service,
)


def build_snapshot() -> dict:
    """Create a valid financial snapshot."""
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


def build_request() -> ScenarioRequest:
    """Create an expense-reduction request."""
    return ScenarioRequest(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name="Dining Reduction",
        description="Reduce dining expenses.",
        parameters={
            "reduction_percentage": 20,
        },
    )


def build_result(
    snapshot: dict,
) -> ScenarioResult:
    """Create a scenario result."""
    projected_snapshot = {
        **snapshot,
        "total_expenses": 2800,
        "net_cash_flow": 2200,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name="Dining Reduction",
        description="Reduce dining expenses.",
        assumptions=[
            ScenarioAssumption(
                name="Reduction Percentage",
                value=20,
            )
        ],
        original_snapshot=snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[
            ScenarioImpact.create(
                metric="Total Expenses",
                original_value=3000,
                projected_value=2800,
            ),
            ScenarioImpact.create(
                metric="Net Cash Flow",
                original_value=2000,
                projected_value=2200,
            ),
        ],
    )


def test_register_handler():
    service = ScenarioService()

    def handler(snapshot, parameters):
        return build_result(snapshot)

    service.register_handler(
        ScenarioType.EXPENSE_REDUCTION,
        handler,
    )

    assert service.has_handler(ScenarioType.EXPENSE_REDUCTION)
    assert service.get_registered_types() == [ScenarioType.EXPENSE_REDUCTION]


def test_run_scenario():
    service = ScenarioService()
    captured: dict = {}

    def handler(snapshot, parameters):
        captured["snapshot"] = snapshot
        captured["parameters"] = parameters
        return build_result(snapshot)

    service.register_handler(
        ScenarioType.EXPENSE_REDUCTION,
        handler,
    )

    result = service.run(
        request=build_request(),
        snapshot=build_snapshot(),
    )

    assert result.scenario_type == ScenarioType.EXPENSE_REDUCTION
    assert captured["parameters"]["reduction_percentage"] == 20
    assert result.projected_snapshot["total_expenses"] == 2800


def test_run_copies_snapshot_and_parameters():
    service = ScenarioService()
    snapshot = build_snapshot()
    request = build_request()

    def handler(handler_snapshot, parameters):
        handler_snapshot["net_worth"] = 999999
        parameters["reduction_percentage"] = 99

        return build_result(build_snapshot())

    service.register_handler(
        ScenarioType.EXPENSE_REDUCTION,
        handler,
    )

    service.run(
        request=request,
        snapshot=snapshot,
    )

    assert snapshot["net_worth"] == 500
    assert request.parameters["reduction_percentage"] == 20


def test_run_rejects_unregistered_handler():
    service = ScenarioService()

    with pytest.raises(
        ValueError,
        match="No handler is registered",
    ):
        service.run(
            request=build_request(),
            snapshot=build_snapshot(),
        )


def test_run_rejects_missing_snapshot_fields():
    service = ScenarioService()

    def handler(snapshot, parameters):
        return build_result(snapshot)

    service.register_handler(
        ScenarioType.EXPENSE_REDUCTION,
        handler,
    )

    incomplete_snapshot = {
        "total_income": 5000,
    }

    with pytest.raises(
        ValueError,
        match="missing required fields",
    ):
        service.run(
            request=build_request(),
            snapshot=incomplete_snapshot,
        )


def test_run_rejects_wrong_result_type():
    service = ScenarioService()

    def handler(snapshot, parameters):
        return ScenarioResult(
            scenario_type=(ScenarioType.INCOME_INCREASE),
            name="Wrong Scenario",
            description="",
            assumptions=[],
            original_snapshot=snapshot,
            projected_snapshot=snapshot,
            impacts=[],
        )

    service.register_handler(
        ScenarioType.EXPENSE_REDUCTION,
        handler,
    )

    with pytest.raises(
        ValueError,
        match="unexpected scenario type",
    ):
        service.run(
            request=build_request(),
            snapshot=build_snapshot(),
        )


def test_clear_handlers():
    service = ScenarioService()

    service.register_handler(
        ScenarioType.EXPENSE_REDUCTION,
        lambda snapshot, parameters: (build_result(snapshot)),
    )

    service.clear_handlers()

    assert service.get_registered_types() == []


def setup_function():
    """Reset shared handlers before each test."""
    reset_scenario_handlers()


def teardown_function():
    """Reset shared handlers after each test."""
    reset_scenario_handlers()


def test_shared_scenario_service():
    register_scenario_handler(
        ScenarioType.EXPENSE_REDUCTION,
        lambda snapshot, parameters: (build_result(snapshot)),
    )

    result = run_financial_scenario(
        request=build_request(),
        snapshot=build_snapshot(),
    )

    assert result.scenario_type == ScenarioType.EXPENSE_REDUCTION

    assert scenario_service.has_handler(ScenarioType.EXPENSE_REDUCTION)

from src.financial.scenarios.combined import (
    detect_plan_conflicts,
    run_combined_scenario_plan,
)
from src.financial.scenarios.models import (
    ScenarioAssumption,
    ScenarioRequest,
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.plan import (
    ScenarioPlanStep,
)
from src.financial.scenarios.service import (
    ScenarioService,
)


def build_snapshot() -> dict:
    """Create a baseline snapshot."""
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


def build_income_request() -> ScenarioRequest:
    """Create an income-increase request."""
    return ScenarioRequest(
        scenario_type=ScenarioType.INCOME_INCREASE,
        name="Income Increase",
        description="",
        parameters={
            "increase_percentage": 10,
        },
    )


def build_expense_request() -> ScenarioRequest:
    """Create an expense-reduction request."""
    return ScenarioRequest(
        scenario_type=ScenarioType.EXPENSE_REDUCTION,
        name="Expense Reduction",
        description="",
        parameters={
            "reduction_percentage": 10,
        },
    )


def build_service() -> ScenarioService:
    """Create a service with simple sequential handlers."""
    service = ScenarioService()

    def income_handler(
        snapshot,
        parameters,
    ):
        increase = 500

        projected = {
            **snapshot,
            "total_income": (snapshot["total_income"] + increase),
            "net_cash_flow": (snapshot["net_cash_flow"] + increase),
            "total_account_balance": (snapshot["total_account_balance"] + 6000),
            "net_worth": (snapshot["net_worth"] + 6000),
        }

        return ScenarioResult(
            scenario_type=ScenarioType.INCOME_INCREASE,
            name="Income Increase",
            description="",
            assumptions=[],
            original_snapshot=snapshot,
            projected_snapshot=projected,
            impacts=[],
            benefits=[
                "Increase monthly income.",
            ],
            recommendations=[
                "Save part of the increase.",
            ],
        )

    def expense_handler(
        snapshot,
        parameters,
    ):
        savings = 300

        projected = {
            **snapshot,
            "total_expenses": (snapshot["total_expenses"] - savings),
            "net_cash_flow": (snapshot["net_cash_flow"] + savings),
            "total_account_balance": (snapshot["total_account_balance"] + 3600),
            "net_worth": (snapshot["net_worth"] + 3600),
        }

        return ScenarioResult(
            scenario_type=(ScenarioType.EXPENSE_REDUCTION),
            name="Expense Reduction",
            description="",
            assumptions=[],
            original_snapshot=snapshot,
            projected_snapshot=projected,
            impacts=[],
            benefits=[
                "Reduce monthly expenses.",
            ],
            recommendations=[
                "Track expenses weekly.",
            ],
        )

    service.register_handler(
        ScenarioType.INCOME_INCREASE,
        income_handler,
    )
    service.register_handler(
        ScenarioType.EXPENSE_REDUCTION,
        expense_handler,
    )

    return service


def test_run_combined_scenario_plan():
    plan = run_combined_scenario_plan(
        name="Growth Plan",
        description="Increase income and reduce expenses.",
        requests=[
            build_income_request(),
            build_expense_request(),
        ],
        snapshot=build_snapshot(),
        service=build_service(),
    )

    assert plan.name == "Growth Plan"
    assert len(plan.steps) == 2
    assert plan.steps[0].result.name == ("Income Increase")
    assert plan.steps[1].result.name == ("Expense Reduction")

    projected = plan.projected_snapshot

    assert projected["total_income"] == 5500
    assert projected["total_expenses"] == 2700
    assert projected["net_cash_flow"] == 2800
    assert projected["total_account_balance"] == 17600
    assert projected["net_worth"] == 10100


def test_scenarios_are_applied_sequentially():
    plan = run_combined_scenario_plan(
        name="Sequential Plan",
        description="",
        requests=[
            build_income_request(),
            build_expense_request(),
        ],
        snapshot=build_snapshot(),
        service=build_service(),
    )

    second_step = plan.steps[1]

    assert second_step.result.original_snapshot["total_income"] == 5500
    assert second_step.result.original_snapshot["net_cash_flow"] == 2500


def test_original_snapshot_is_not_mutated():
    snapshot = build_snapshot()

    run_combined_scenario_plan(
        name="Growth Plan",
        description="",
        requests=[
            build_income_request(),
            build_expense_request(),
        ],
        snapshot=snapshot,
        service=build_service(),
    )

    assert snapshot == build_snapshot()


def test_combined_report_contains_cumulative_changes():
    plan = run_combined_scenario_plan(
        name="Growth Plan",
        description="",
        requests=[
            build_income_request(),
            build_expense_request(),
        ],
        snapshot=build_snapshot(),
        service=build_service(),
    )

    assert plan.get_metric_change("Net Worth") == 9600
    assert plan.get_metric_change("Net Cash Flow") == 800
    assert plan.get_metric_change("Total Expenses") == -300


def test_combined_guidance_is_aggregated():
    plan = run_combined_scenario_plan(
        name="Growth Plan",
        description="",
        requests=[
            build_income_request(),
            build_expense_request(),
        ],
        snapshot=build_snapshot(),
        service=build_service(),
    )

    assert plan.benefits == [
        "Increase monthly income.",
        "Reduce monthly expenses.",
    ]
    assert plan.recommendations == [
        "Save part of the increase.",
        "Track expenses weekly.",
    ]


def test_rejects_empty_plan_name():
    try:
        run_combined_scenario_plan(
            name=" ",
            description="",
            requests=[
                build_income_request(),
            ],
            snapshot=build_snapshot(),
            service=build_service(),
        )
    except ValueError as error:
        assert "name cannot be empty" in str(error)
    else:
        raise AssertionError("Expected a ValueError.")


def test_rejects_empty_request_list():
    try:
        run_combined_scenario_plan(
            name="Empty Plan",
            description="",
            requests=[],
            snapshot=build_snapshot(),
            service=build_service(),
        )
    except ValueError as error:
        assert "At least one scenario request" in str(error)
    else:
        raise AssertionError("Expected a ValueError.")


def test_detects_commitment_conflict():
    snapshot = build_snapshot()

    savings_result = ScenarioResult(
        scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
        name="Additional Savings",
        description="",
        assumptions=[
            ScenarioAssumption(
                name="Additional Monthly Savings",
                value=1500,
            )
        ],
        original_snapshot=snapshot,
        projected_snapshot={
            **snapshot,
            "net_cash_flow": 500,
        },
        impacts=[],
    )

    debt_result = ScenarioResult(
        scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
        name="Extra Debt Payment",
        description="",
        assumptions=[
            ScenarioAssumption(
                name="Extra Monthly Payment",
                value=1000,
            )
        ],
        original_snapshot=(savings_result.projected_snapshot),
        projected_snapshot={
            **savings_result.projected_snapshot,
            "net_cash_flow": -500,
        },
        impacts=[],
    )

    steps = [
        ScenarioPlanStep(
            order=1,
            request=ScenarioRequest(
                scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
                name="Additional Savings",
                description="",
                parameters={},
            ),
            result=savings_result,
        ),
        ScenarioPlanStep(
            order=2,
            request=ScenarioRequest(
                scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
                name="Extra Debt Payment",
                description="",
                parameters={},
            ),
            result=debt_result,
        ),
    ]

    conflicts = detect_plan_conflicts(
        snapshot,
        debt_result.projected_snapshot,
        steps,
    )

    assert any(
        "exceed the original monthly net cash flow" in conflict
        for conflict in conflicts
    )
    assert any("negative monthly net cash flow" in conflict for conflict in conflicts)

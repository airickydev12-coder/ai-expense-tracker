import pytest

from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.optimizer import (
    OptimizationCandidate,
    OptimizationFailure,
    generate_optimization_candidates,
    optimize_financial_snapshot,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
)
from src.financial.scenarios.service import (
    ScenarioService,
)


def build_snapshot() -> dict:
    """Create a snapshot for optimizer tests."""
    return {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 8000,
        "total_goal_progress": 2500,
        "total_debt": 15000,
        "net_worth": -4500,
        "health_score": 65,
        "health_status": "Fair",
        "category_totals": {
            "Food": 600,
            "Housing": 1500,
        },
        "debts": [
            {
                "id": 1,
                "name": "Credit Card",
                "balance": 10000,
                "interest_rate": 18,
                "minimum_payment": 300,
            },
            {
                "id": 2,
                "name": "Student Loan",
                "balance": 5000,
                "interest_rate": 4,
                "minimum_payment": 100,
            },
        ],
    }


def build_service() -> ScenarioService:
    """Create a controlled optimizer test service."""
    service = ScenarioService()

    def expense_handler(
        snapshot,
        parameters,
    ):
        percentage = float(parameters["reduction_percentage"])

        improvement = percentage * 10

        projected = {
            **snapshot,
            "total_expenses": (snapshot["total_expenses"] - improvement),
            "net_cash_flow": (snapshot["net_cash_flow"] + improvement),
            "total_account_balance": (
                snapshot["total_account_balance"] + improvement * 12
            ),
            "net_worth": (snapshot["net_worth"] + improvement * 12),
        }

        return ScenarioResult(
            scenario_type=(ScenarioType.EXPENSE_REDUCTION),
            name=("Expense Candidate " f"{percentage:g}"),
            description="",
            assumptions=[],
            original_snapshot=snapshot,
            projected_snapshot=projected,
            impacts=[],
        )

    def income_handler(
        snapshot,
        parameters,
    ):
        percentage = float(parameters["increase_percentage"])

        improvement = percentage * 50

        projected = {
            **snapshot,
            "total_income": (snapshot["total_income"] + improvement),
            "net_cash_flow": (snapshot["net_cash_flow"] + improvement),
            "total_account_balance": (
                snapshot["total_account_balance"] + improvement * 12
            ),
            "net_worth": (snapshot["net_worth"] + improvement * 12),
        }

        return ScenarioResult(
            scenario_type=(ScenarioType.INCOME_INCREASE),
            name=("Income Candidate " f"{percentage:g}"),
            description="",
            assumptions=[],
            original_snapshot=snapshot,
            projected_snapshot=projected,
            impacts=[],
        )

    def savings_handler(
        snapshot,
        parameters,
    ):
        amount = float(parameters["additional_monthly_savings"])

        projected = {
            **snapshot,
            "net_cash_flow": (snapshot["net_cash_flow"] - amount),
            "total_account_balance": (snapshot["total_account_balance"] + amount * 12),
            "total_goal_progress": (snapshot["total_goal_progress"] + amount * 12),
            "net_worth": (snapshot["net_worth"] + amount * 12),
        }

        return ScenarioResult(
            scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
            name=("Savings Candidate " f"{amount:g}"),
            description="",
            assumptions=[],
            original_snapshot=snapshot,
            projected_snapshot=projected,
            impacts=[],
        )

    def debt_handler(
        snapshot,
        parameters,
    ):
        amount = float(parameters["extra_monthly_payment"])

        debt_reduction = amount * 12

        projected = {
            **snapshot,
            "net_cash_flow": (snapshot["net_cash_flow"] - amount),
            "total_debt": max(
                snapshot["total_debt"] - debt_reduction,
                0,
            ),
            "net_worth": (snapshot["net_worth"] + debt_reduction),
        }

        return ScenarioResult(
            scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
            name=("Debt Candidate " f"{amount:g}"),
            description="",
            assumptions=[],
            original_snapshot=snapshot,
            projected_snapshot=projected,
            impacts=[],
        )

    service.register_handler(
        ScenarioType.EXPENSE_REDUCTION,
        expense_handler,
    )

    service.register_handler(
        ScenarioType.INCOME_INCREASE,
        income_handler,
    )

    service.register_handler(
        ScenarioType.ADDITIONAL_SAVINGS,
        savings_handler,
    )

    service.register_handler(
        ScenarioType.EXTRA_DEBT_PAYMENT,
        debt_handler,
    )

    return service


def test_optimization_candidate():
    candidate = OptimizationCandidate(
        request=(
            generate_optimization_candidates(
                build_snapshot(),
                expense_reduction_percentages=(10,),
                income_increase_percentages=(),
                additional_savings_amounts=(),
                extra_debt_payments=(),
            )[0].request
        ),
        source="Expense Optimization",
        rationale="Reduce a large spending category.",
    )

    assert candidate.source == ("Expense Optimization")
    assert candidate.rationale
    assert "request" in candidate.to_dict()


def test_optimization_candidate_rejects_empty_source():
    request = generate_optimization_candidates(
        build_snapshot(),
        expense_reduction_percentages=(10,),
        income_increase_percentages=(),
        additional_savings_amounts=(),
        extra_debt_payments=(),
    )[0].request

    with pytest.raises(
        ValueError,
        match="source cannot be empty",
    ):
        OptimizationCandidate(
            request=request,
            source=" ",
            rationale="Valid rationale.",
        )


def test_optimization_failure():
    failure = OptimizationFailure(
        candidate_name="Income Increase",
        error="Unable to evaluate.",
    )

    assert failure.candidate_name == ("Income Increase")
    assert failure.to_dict()["error"] == ("Unable to evaluate.")


def test_generate_optimization_candidates():
    candidates = generate_optimization_candidates(
        build_snapshot(),
        expense_reduction_percentages=(10,),
        income_increase_percentages=(5,),
        additional_savings_amounts=(100,),
        extra_debt_payments=(250,),
    )

    scenario_types = {candidate.request.scenario_type for candidate in candidates}

    assert ScenarioType.EXPENSE_REDUCTION in (scenario_types)
    assert ScenarioType.INCOME_INCREASE in (scenario_types)
    assert ScenarioType.ADDITIONAL_SAVINGS in (scenario_types)
    assert ScenarioType.EXTRA_DEBT_PAYMENT in (scenario_types)

    assert len(candidates) == 6


def test_expense_candidates_generated_for_each_category():
    candidates = generate_optimization_candidates(
        build_snapshot(),
        expense_reduction_percentages=(
            10,
            20,
        ),
        income_increase_percentages=(),
        additional_savings_amounts=(),
        extra_debt_payments=(),
    )

    assert len(candidates) == 4

    names = {candidate.request.name for candidate in candidates}

    assert "Reduce Food by 10%" in names
    assert "Reduce Food by 20%" in names
    assert "Reduce Housing by 10%" in names
    assert "Reduce Housing by 20%" in names


def test_debt_candidates_generated_for_each_debt():
    candidates = generate_optimization_candidates(
        build_snapshot(),
        expense_reduction_percentages=(),
        income_increase_percentages=(),
        additional_savings_amounts=(),
        extra_debt_payments=(100,),
    )

    assert len(candidates) == 2

    debt_ids = {candidate.request.parameters["debt_id"] for candidate in candidates}

    assert debt_ids == {
        1,
        2,
    }


def test_savings_candidates_do_not_exceed_cash_flow():
    snapshot = build_snapshot()
    snapshot["net_cash_flow"] = 200

    candidates = generate_optimization_candidates(
        snapshot,
        expense_reduction_percentages=(),
        income_increase_percentages=(),
        additional_savings_amounts=(
            100,
            250,
            500,
        ),
        extra_debt_payments=(),
    )

    amounts = [
        candidate.request.parameters["additional_monthly_savings"]
        for candidate in candidates
    ]

    assert amounts == [
        100.0,
    ]


def test_generate_candidates_normalizes_values():
    candidates = generate_optimization_candidates(
        build_snapshot(),
        expense_reduction_percentages=(
            -10,
            10,
            10,
        ),
        income_increase_percentages=(),
        additional_savings_amounts=(),
        extra_debt_payments=(),
    )

    assert len(candidates) == 2


def test_generate_candidates_rejects_invalid_horizon():
    with pytest.raises(
        ValueError,
        match="greater than zero months",
    ):
        generate_optimization_candidates(
            build_snapshot(),
            horizon_months=0,
        )


def test_optimize_financial_snapshot():
    result = optimize_financial_snapshot(
        build_snapshot(),
        service=build_service(),
        register_handlers=False,
        expense_reduction_percentages=(10,),
        income_increase_percentages=(5,),
        additional_savings_amounts=(100,),
        extra_debt_payments=(250,),
    )

    assert result.candidate_count == 6
    assert result.success_count == 6
    assert result.failure_count == 0
    assert len(result.ranked_scenarios) == 6
    assert result.best_scenario is not None


def test_optimizer_ranks_candidates():
    result = optimize_financial_snapshot(
        build_snapshot(),
        service=build_service(),
        register_handlers=False,
        ranking_metric=(ScenarioRankingMetric.NET_WORTH),
        expense_reduction_percentages=(10,),
        income_increase_percentages=(5,),
        additional_savings_amounts=(100,),
        extra_debt_payments=(250,),
    )

    assert result.best_scenario is not None

    assert result.best_scenario.score == max(
        ranked.score for ranked in result.ranked_scenarios
    )


def test_optimizer_applies_result_limit():
    result = optimize_financial_snapshot(
        build_snapshot(),
        service=build_service(),
        register_handlers=False,
        limit=3,
        expense_reduction_percentages=(10,),
        income_increase_percentages=(5,),
        additional_savings_amounts=(100,),
        extra_debt_payments=(250,),
    )

    assert len(result.ranked_scenarios) == 3
    assert result.success_count == 6


def test_optimizer_rejects_invalid_limit():
    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        optimize_financial_snapshot(
            build_snapshot(),
            service=build_service(),
            register_handlers=False,
            limit=0,
        )


def test_optimizer_records_candidate_failures():
    service = build_service()

    def failing_income_handler(
        snapshot,
        parameters,
    ):
        raise ValueError("Income scenario failed.")

    service.register_handler(
        ScenarioType.INCOME_INCREASE,
        failing_income_handler,
    )

    result = optimize_financial_snapshot(
        build_snapshot(),
        service=service,
        register_handlers=False,
        expense_reduction_percentages=(),
        income_increase_percentages=(5,),
        additional_savings_amounts=(),
        extra_debt_payments=(),
    )

    assert result.candidate_count == 1
    assert result.success_count == 0
    assert result.failure_count == 1
    assert result.best_scenario is None

    assert result.failures[0].error == ("Income scenario failed.")


def test_optimizer_does_not_mutate_snapshot():
    snapshot = build_snapshot()

    optimize_financial_snapshot(
        snapshot,
        service=build_service(),
        register_handlers=False,
        expense_reduction_percentages=(10,),
        income_increase_percentages=(),
        additional_savings_amounts=(),
        extra_debt_payments=(),
    )

    assert snapshot == build_snapshot()


def test_optimization_result_serialization():
    result = optimize_financial_snapshot(
        build_snapshot(),
        service=build_service(),
        register_handlers=False,
        limit=2,
        expense_reduction_percentages=(10,),
        income_increase_percentages=(5,),
        additional_savings_amounts=(),
        extra_debt_payments=(),
    )

    data = result.to_dict()

    assert data["candidate_count"] == 3
    assert data["success_count"] == 3
    assert data["failure_count"] == 0
    assert len(data["ranked_scenarios"]) == 2
    assert data["best_scenario"] is not None

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.financial.budgets.models import Budget
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.recommendations.history import RecommendationRecord
from src.financial.recommendations.status import RecommendationStatus
from src.financial.shared.categories import ExpenseCategory
from src.presentation import views
from src.financial.forecasting.models import (
    FinancialForecast,
    MetricProjection,
)

from src.financial.scenarios.models import (
    ScenarioAssumption,
    ScenarioImpact,
    ScenarioRequest,
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.optimizer import (
    OptimizationFailure,
    OptimizationResult,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
    rank_scenarios,
)
from src.financial.scenarios.plan import (
    ScenarioPlanResult,
    build_cumulative_scenario_report,
)


def build_history() -> list[FinancialSnapshotRecord]:
    """Create financial history for view tests."""
    now = datetime.now(timezone.utc)

    return [
        FinancialSnapshotRecord(
            timestamp=now - timedelta(days=30),
            total_income=Decimal("4000"),
            total_expenses=Decimal("2000"),
            net_cash_flow=Decimal("2000"),
            total_account_balance=Decimal("1500"),
            total_goal_progress=Decimal("1000"),
            total_debt=Decimal("2000"),
            net_worth=Decimal("500"),
            health_score=60,
            health_status="Fair",
        ),
        FinancialSnapshotRecord(
            timestamp=now,
            total_income=Decimal("5000"),
            total_expenses=Decimal("1800"),
            net_cash_flow=Decimal("3200"),
            total_account_balance=Decimal("2500"),
            total_goal_progress=Decimal("2000"),
            total_debt=Decimal("1500"),
            net_worth=Decimal("3000"),
            health_score=80,
            health_status="Good",
        ),
    ]


def build_scenario_result() -> ScenarioResult:
    """Create a scenario result for view tests."""
    original_snapshot = {
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

    projected_snapshot = {
        **original_snapshot,
        "total_expenses": 2800,
        "net_cash_flow": 2200,
        "total_account_balance": 10400,
        "net_worth": 2900,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name="Food Expense Reduction",
        description="Reduce food spending.",
        assumptions=[
            ScenarioAssumption(
                name="Reduction Percentage",
                value=20,
                description=("Reduce monthly food spending."),
            )
        ],
        original_snapshot=original_snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[
            ScenarioImpact.create(
                metric="Monthly Savings",
                original_value=0,
                projected_value=200,
            )
        ],
        benefits=[
            "Increase monthly available cash flow.",
        ],
        risks=[
            "The reduction may be difficult to maintain.",
        ],
        recommendations=[
            "Track food spending weekly.",
        ],
    )


def test_display_scenario_result_includes_comparison_report(
    capsys,
):
    views.display_scenario_result(build_scenario_result())

    output = capsys.readouterr().out

    assert "Financial Scenario" in output
    assert "Food Expense Reduction" in output
    assert "Scenario Comparison" in output
    assert "overall improvement" in output
    assert "Metric Comparisons" in output
    assert "Total Expenses" in output
    assert "Net Cash Flow" in output
    assert "Account Balance" in output
    assert "Net Worth" in output
    assert "Improvement" in output


def test_display_scenario_result_includes_summary_counts(
    capsys,
):
    views.display_scenario_result(build_scenario_result())

    output = capsys.readouterr().out

    assert "Comparison Summary" in output
    assert "Improvements:          4" in output
    assert "Declines:              0" in output
    assert "Unchanged:             4" in output


def test_display_scenario_result_preserves_specific_impacts(
    capsys,
):
    views.display_scenario_result(build_scenario_result())

    output = capsys.readouterr().out

    assert "Scenario-Specific Impacts" in output
    assert "Monthly Savings" in output
    assert "Projected:             200.00" in output


def test_display_scenario_result_includes_guidance(
    capsys,
):
    views.display_scenario_result(build_scenario_result())

    output = capsys.readouterr().out

    assert "Benefits" in output
    assert "Increase monthly available cash flow." in output
    assert "Risks" in output
    assert "The reduction may be difficult to maintain." in output
    assert "Recommendations" in output
    assert "Track food spending weekly." in output


def test_display_current_budgets(
    monkeypatch,
    capsys,
):
    budgets = [
        Budget(
            category=ExpenseCategory.FOOD,
            limit=Decimal("500"),
        ),
        Budget(
            category=ExpenseCategory.TRANSPORTATION,
            limit=Decimal("300"),
        ),
    ]

    monkeypatch.setattr(
        views,
        "get_budgets",
        lambda: budgets,
    )

    views.display_current_budgets()

    output = capsys.readouterr().out

    assert "Current Budgets" in output
    assert "Food" in output
    assert "Transportation" in output


def test_show_menu_includes_financial_trends(
    capsys,
):
    views.show_menu()

    output = capsys.readouterr().out

    assert "9. View Financial Snapshot" in output
    assert "10. Manage Recommendations" in output
    assert "11. View Financial Trends" in output
    assert "12. View Financial Forecast" in output
    assert "13. Model Financial Scenarios" in output
    assert "14. AI Financial Coach" in output
    assert "15. Exit" in output


def test_recommendation_management_menu(
    capsys,
):
    views.display_recommendation_management_menu()

    output = capsys.readouterr().out

    assert "View Active Recommendations" in output
    assert "Mark Recommendation Completed" in output
    assert "Suppress Recommendation" in output
    assert "7. Back" in output


def test_display_recommendations(
    capsys,
):
    recommendations = [
        {
            "key": "debt:high_interest_debt",
            "priority": "HIGH",
            "category": "Debt",
            "title": "High Interest Debt",
            "message": "You have high-interest debt.",
            "action": "Prioritize repayment.",
        }
    ]

    views.display_recommendations(recommendations)

    output = capsys.readouterr().out

    assert "Active Recommendations" in output
    assert "High Interest Debt" in output
    assert "debt:high_interest_debt" in output
    assert "Prioritize repayment" in output


def test_display_recommendations_when_empty(
    capsys,
):
    views.display_recommendations([])

    output = capsys.readouterr().out

    assert "No active recommendations are available." in output


def test_display_recommendation_history(
    capsys,
):
    timestamp = datetime.now(timezone.utc)

    records = [
        RecommendationRecord(
            recommendation_key=("debt:high_interest_debt"),
            status=RecommendationStatus.COMPLETED,
            created_at=timestamp,
            updated_at=timestamp,
            note="Debt paid off.",
        )
    ]

    views.display_recommendation_history(records)

    output = capsys.readouterr().out

    assert "Recommendation History" in output
    assert "COMPLETED" in output
    assert "debt:high_interest_debt" in output
    assert "Debt paid off." in output


def test_display_recommendation_history_empty(
    capsys,
):
    views.display_recommendation_history([])

    output = capsys.readouterr().out

    assert "No recommendation history is available." in output


def test_display_financial_snapshot(
    capsys,
):
    snapshot = {
        "total_income": 5000,
        "total_expenses": 1500,
        "net_cash_flow": 3500,
        "total_account_balance": 2000,
        "total_goal_progress": 2500,
        "total_debt": 1000,
        "net_worth": 3500,
        "health_score": 85,
        "health_status": "Excellent",
        "accounts": [{}],
        "goals": [{}],
        "debts": [{}],
        "bills": [{}],
        "recommendations": [
            {
                "priority": "HIGH",
                "category": "Debt",
                "title": "High Interest Debt",
                "message": "Debt detected.",
                "action": "Prioritize repayment.",
            }
        ],
    }

    views.display_financial_snapshot(snapshot)

    output = capsys.readouterr().out

    assert "Financial Snapshot" in output
    assert "$5000.00" in output
    assert "$3500.00" in output
    assert "85 (Excellent)" in output
    assert "High Interest Debt" in output


def test_display_financial_trends(
    capsys,
):
    views.display_financial_trends(build_history())

    output = capsys.readouterr().out

    assert "Financial Trends" in output
    assert "Snapshots Recorded:" in output
    assert "2" in output
    assert "Net Worth Change:" in output
    assert "+$2,500.00" in output
    assert "Cash Flow Change:" in output
    assert "+$1,200.00" in output
    assert "Income Change:" in output
    assert "+$1,000.00" in output
    assert "Expense Change:" in output
    assert "-$200.00" in output
    assert "Health Score Change:" in output
    assert "+20" in output


def test_display_financial_trends_without_history(
    capsys,
):
    views.display_financial_trends([])

    output = capsys.readouterr().out

    assert "No financial snapshots have been recorded." in output


def test_display_financial_trends_with_one_snapshot(
    capsys,
):
    history = [build_history()[0]]

    views.display_financial_trends(history)

    output = capsys.readouterr().out

    assert "Snapshots Recorded:" in output
    assert "Record at least two snapshots" in output


def test_display_financial_trends_includes_intelligence(
    capsys,
):
    views.display_financial_trends(build_history())

    output = capsys.readouterr().out

    assert "Trend Intelligence" in output
    assert "Overall Momentum:      Positive" in output
    assert "Net Worth Trend:       Improving" in output
    assert "Cash Flow Trend:       Improving" in output
    assert "Income Trend:          Improving" in output
    assert "Expense Trend:         Improving" in output
    assert "Health Trend:          Improving" in output


def build_forecast() -> FinancialForecast:
    """Create a financial forecast for view tests."""
    return FinancialForecast(
        generated_at=datetime(
            2026,
            7,
            14,
            20,
            10,
            tzinfo=timezone.utc,
        ),
        horizon_days=90,
        history_points=6,
        net_worth=MetricProjection(
            metric="Net Worth",
            current_value=Decimal("12500"),
            projected_value=Decimal("18200"),
            projected_change=Decimal("5700"),
            daily_change=Decimal("63.333333"),
            horizon_days=90,
        ),
        cash_flow=MetricProjection(
            metric="Cash Flow",
            current_value=Decimal("1200"),
            projected_value=Decimal("1350"),
            projected_change=Decimal("150"),
            daily_change=Decimal("1.666667"),
            horizon_days=90,
        ),
        account_balance=MetricProjection(
            metric="Account Balance",
            current_value=Decimal("8000"),
            projected_value=Decimal("9200"),
            projected_change=Decimal("1200"),
            daily_change=Decimal("13.333333"),
            horizon_days=90,
        ),
        goal_progress=MetricProjection(
            metric="Goal Progress",
            current_value=Decimal("4000"),
            projected_value=Decimal("5500"),
            projected_change=Decimal("1500"),
            daily_change=Decimal("16.666667"),
            horizon_days=90,
        ),
        total_debt=MetricProjection(
            metric="Total Debt",
            current_value=Decimal("8500"),
            projected_value=Decimal("6100"),
            projected_change=Decimal("-2400"),
            daily_change=Decimal("-26.666667"),
            horizon_days=90,
        ),
        health_score=MetricProjection(
            metric="Health Score",
            current_value=Decimal("72"),
            projected_value=Decimal("81"),
            projected_change=Decimal("9"),
            daily_change=Decimal("0.1"),
            horizon_days=90,
        ),
    )


def test_show_menu_includes_financial_forecast(
    capsys,
):
    views.show_menu()

    output = capsys.readouterr().out

    assert "11. View Financial Trends" in output
    assert "12. View Financial Forecast" in output
    assert "13. Model Financial Scenarios" in output
    assert "14. AI Financial Coach" in output
    assert "15. Exit" in output


def test_display_financial_forecast(
    capsys,
):
    views.display_financial_forecast(build_forecast())

    output = capsys.readouterr().out

    assert "Financial Forecast" in output
    assert "Forecast Horizon:      90 days" in output
    assert "History Points:        6" in output
    assert "Generated:             2026-07-14 20:10" in output
    assert "Net Worth" in output
    assert "$12,500.00" in output
    assert "$18,200.00" in output
    assert "+$5,700.00" in output
    assert "Total Debt" in output
    assert "-$2,400.00" in output
    assert "Health Score" in output
    assert "+9" in output
    assert "historical linear trends" in output


def test_display_forecast_with_one_history_point(
    capsys,
):
    forecast = build_forecast()

    single_point_forecast = FinancialForecast(
        generated_at=forecast.generated_at,
        horizon_days=forecast.horizon_days,
        history_points=1,
        net_worth=forecast.net_worth,
        cash_flow=forecast.cash_flow,
        account_balance=forecast.account_balance,
        goal_progress=forecast.goal_progress,
        total_debt=forecast.total_debt,
        health_score=forecast.health_score,
    )

    views.display_financial_forecast(single_point_forecast)

    output = capsys.readouterr().out

    assert "Only one historical snapshot is available." in output
    assert "until more history is recorded" in output


def test_display_combined_plan_steps(
    capsys,
):
    requests = [
        ScenarioRequest(
            scenario_type=(ScenarioType.INCOME_INCREASE),
            name="Income Increase",
            description="",
            parameters={},
        )
    ]

    views.display_combined_plan_steps(requests)

    output = capsys.readouterr().out

    assert "Combined Plan Steps" in output
    assert "Income Increase" in output


def test_display_combined_plan_steps_when_empty(
    capsys,
):
    views.display_combined_plan_steps([])

    output = capsys.readouterr().out

    assert "No scenario steps have been added." in output


def test_display_combined_plan_result(
    capsys,
):
    original = {
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

    projected = {
        **original,
        "total_income": 5500,
        "net_cash_flow": 2500,
        "total_debt": 9000,
        "net_worth": 6500,
    }

    plan = ScenarioPlanResult(
        name="Growth Plan",
        description="Increase income and reduce debt.",
        original_snapshot=original,
        projected_snapshot=projected,
        steps=[],
        cumulative_report=(
            build_cumulative_scenario_report(
                original,
                projected,
            )
        ),
        benefits=[
            "Improve financial capacity.",
        ],
        conflicts=[],
    )

    views.display_combined_plan_result(plan)

    output = capsys.readouterr().out

    assert "Combined Financial Plan" in output
    assert "Growth Plan" in output
    assert "Cumulative Comparison" in output
    assert "Net Worth Change:" in output
    assert "+$6,000.00" in output
    assert "Cash Flow Change:" in output
    assert "+$500.00" in output
    assert "Debt Reduction:" in output
    assert "$1,000.00" in output
    assert "No conflicts detected." in output


def test_display_scenario_management_menu(
    capsys,
):
    """Verify the scenario-management menu options."""
    views.display_scenario_management_menu()

    output = capsys.readouterr().out

    assert "1. Reduce an Expense Category" in output
    assert "2. Increase Income" in output
    assert "3. Add Monthly Savings" in output
    assert "4. Make an Extra Debt Payment" in output
    assert "5. Build Combined Plan" in output
    assert "6. Run Financial Optimizer" in output
    assert "7. Open Planning Workspace" in output
    assert "8. Back" in output


def build_optimizer_result() -> OptimizationResult:
    """Create an optimization result for view tests."""
    original = {
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

    projected = {
        **original,
        "total_income": 5500,
        "net_cash_flow": 2500,
        "total_account_balance": 14000,
        "net_worth": 6500,
        "health_score": 82,
    }

    scenario = ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Increase Income by 10%",
        description="",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
    )

    ranked = rank_scenarios(
        [
            scenario,
        ],
        ScenarioRankingMetric.OVERALL,
    )

    return OptimizationResult(
        snapshot=original,
        candidates=[],
        successful_results=[
            scenario,
        ],
        ranked_scenarios=ranked,
        failures=[],
        ranking_metric=(ScenarioRankingMetric.OVERALL),
    )


def test_display_optimizer_menu(
    capsys,
):
    """Verify the financial optimizer menu."""
    views.display_optimizer_menu()

    output = capsys.readouterr().out

    assert "Financial Plan Optimizer" in output
    assert "1. Optimize Overall Plan" in output
    assert "2. Maximize Net Worth" in output
    assert "3. Improve Cash Flow" in output
    assert "4. Reduce Debt" in output
    assert "5. Find Lowest-Risk Option" in output
    assert "6. Find Most Sustainable Option" in output
    assert "7. Back" in output


def test_display_optimizer_result(
    capsys,
):
    """Verify a successful optimizer result display."""
    views.display_optimizer_result(build_optimizer_result())

    output = capsys.readouterr().out

    assert "Financial Optimization" in output
    assert "Ranking Objective:" in output
    assert "Candidates Generated:" in output
    assert "Ranked Recommendations" in output
    assert "Increase Income by 10%" in output
    assert "Overall Score:" in output
    assert "Risk:" in output
    assert "Sustainability:" in output
    assert "Best Recommended Scenario" in output
    assert "Score Components" in output


def test_display_optimizer_result_with_failure(
    capsys,
):
    """Verify optimizer candidate failures are displayed."""
    result = build_optimizer_result()

    result_with_failure = OptimizationResult(
        snapshot=result.snapshot,
        candidates=result.candidates,
        successful_results=(result.successful_results),
        ranked_scenarios=(result.ranked_scenarios),
        failures=[
            OptimizationFailure(
                candidate_name="Debt Candidate",
                error="Unable to amortize debt.",
            )
        ],
        ranking_metric=result.ranking_metric,
    )

    views.display_optimizer_result(result_with_failure)

    output = capsys.readouterr().out

    assert "Candidate Failures" in output
    assert "Debt Candidate" in output
    assert "Unable to amortize debt." in output

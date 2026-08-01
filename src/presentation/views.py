from decimal import Decimal

from src.financial.budgets.service import get_budgets
from src.financial.expenses.analytics import (
    get_average,
    get_category_totals,
    get_highest_expense,
    get_total,
)
from src.financial.expenses.service import get_expenses
from src.financial.forecasting.models import (
    FinancialForecast,
    MetricProjection,
)
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.trends import analyze_financial_trends
from src.financial.recommendations.history import RecommendationRecord
from src.financial.reports.budget_report import build_budget_report
from src.financial.scenarios.comparison import (
    METRIC_NET_CASH_FLOW,
    METRIC_NET_WORTH,
    METRIC_TOTAL_DEBT,
)
from src.financial.scenarios.formatter import (
    format_metric_comparison,
)
from src.financial.scenarios.models import (
    ScenarioImpact,
    ScenarioRequest,
    ScenarioResult,
)
from src.financial.scenarios.optimizer import (
    OptimizationResult,
)
from src.financial.scenarios.plan import (
    ScenarioPlanResult,
)
from src.financial.scenarios.report import (
    build_scenario_comparison_report,
)
from src.financial.scenarios.scoring import (
    ScenarioScore,
)
from src.financial.shared.categories import ExpenseCategory


def _format_signed_currency(value: Decimal) -> str:
    """Format a currency change with an explicit sign."""
    if value > 0:
        return f"+${value:,.2f}"

    if value < 0:
        return f"-${abs(value):,.2f}"

    return "$0.00"


def _format_signed_number(value: int) -> str:
    """Format a numeric change with an explicit sign."""
    if value > 0:
        return f"+{value}"

    return str(value)


def display_dashboard() -> None:
    """Display a financial dashboard summary."""
    expenses = get_expenses()

    if not expenses:
        print("\nFinancial Core")
        print("No expenses recorded yet.")
        return

    total = get_total(expenses)
    average = get_average(expenses)
    highest = get_highest_expense(expenses)
    category_totals = get_category_totals(expenses)
    budgets = get_budgets()
    budget_report = build_budget_report(
        budgets,
        expenses,
    )

    print("\n==============================")
    print("        Financial Core")
    print("==============================")
    print(f"Expenses:           {len(expenses)}")
    print(f"Total Spending:     ${total:.2f}")
    print(f"Average Expense:    ${average:.2f}")

    if highest is not None:
        print(f"Largest Expense:    " f"{highest.name} - " f"${highest.amount:.2f}")

    if category_totals:
        top_category = max(
            category_totals,
            key=lambda category: category_totals[category],
        )

        print(
            f"Top Category:       "
            f"{top_category} - "
            f"${category_totals[top_category]:.2f}"
        )

    if budget_report:
        print("\nBudget Status:")

        for summary in budget_report:
            print(
                f"{summary['category']}: "
                f"{summary['status']} "
                f"(${summary['remaining']:.2f} remaining)"
            )

    print("==============================")


def show_menu() -> None:
    """Display the main menu."""
    print("\nFinancial Core")
    print("1. Add Expense")
    print("2. View Expenses")
    print("3. View Total Spending")
    print("4. Delete Expense")
    print("5. Update Expense")
    print("6. View Category Totals")
    print("7. Manage Budgets")
    print("8. View Budget Report")
    print("9. View Financial Snapshot")
    print("10. Manage Recommendations")
    print("11. View Financial Trends")
    print("12. View Financial Forecast")
    print("13. Model Financial Scenarios")
    print("14. AI Financial Coach")
    print("15. Exit")


def display_recommendation_management_menu() -> None:
    """Display the recommendation-management menu."""
    print("\nManage Recommendations")
    print("1. View Active Recommendations")
    print("2. View Recommendation History")
    print("3. Mark Recommendation Active")
    print("4. Mark Recommendation Completed")
    print("5. Dismiss Recommendation")
    print("6. Suppress Recommendation")
    print("7. Back")


def display_categories() -> None:
    """Display available expense categories."""
    print("\nCategories:")

    for index, category in enumerate(
        ExpenseCategory,
        start=1,
    ):
        print(f"{index}. {category.value}")


def display_expenses() -> None:
    """Display all recorded expenses."""
    expenses = get_expenses()

    if not expenses:
        print("No expenses recorded yet.")
        return

    print("\nExpenses:")

    for expense in expenses:
        print(
            f"ID {expense.id}: "
            f"{expense.name} | "
            f"{expense.category.value} | "
            f"${expense.amount:.2f}"
        )


def display_category_totals() -> None:
    """Display spending totals by category."""
    totals = get_category_totals(get_expenses())

    if not totals:
        print("No expenses recorded yet.")
        return

    print("\nCategory Totals:")

    for category, total in totals.items():
        print(f"{category}: ${total:.2f}")


def display_budget_summary(
    summary: dict,
) -> None:
    """Display one budget summary."""
    print("\nBudget Summary:")
    print(f"Category:  {summary['category']}")
    print(f"Limit:     ${summary['limit']:.2f}")
    print(f"Spent:     ${summary['spent']:.2f}")
    print(f"Remaining: " f"${summary['remaining']:.2f}")
    print(f"Status:    {summary['status']}")


def display_saved_budget_summaries() -> None:
    """Display summaries for saved budgets."""
    budgets = get_budgets()
    expenses = get_expenses()

    if not budgets:
        print("No budgets configured yet.")
        return

    report = build_budget_report(
        budgets,
        expenses,
    )

    print("\nBudget Report:")

    for summary in report:
        print(
            f"{summary['category']}: "
            f"Limit ${summary['limit']:.2f} | "
            f"Spent ${summary['spent']:.2f} | "
            f"Remaining ${summary['remaining']:.2f} | "
            f"{summary['status']}"
        )


def display_current_budgets() -> None:
    """Display all configured budgets."""
    budgets = get_budgets()

    if not budgets:
        print("\nNo budgets have been created yet.")
        return

    print("\nCurrent Budgets")
    print("----------------")

    for budget in budgets:
        print(f"{budget.category.value:<20}" f"${budget.limit:>8.2f}")


def display_recommendations(
    recommendations: list[dict],
) -> None:
    """Display active serialized recommendations."""
    print("\nActive Recommendations")
    print("----------------------------------------")

    if not recommendations:
        print("No active recommendations " "are available.")
        return

    for index, recommendation in enumerate(
        recommendations,
        start=1,
    ):
        priority = recommendation.get(
            "priority",
            "UNKNOWN",
        )
        category = recommendation.get(
            "category",
            "General",
        )
        title = recommendation.get(
            "title",
            "Recommendation",
        )
        message = recommendation.get(
            "message",
            "",
        )
        action = recommendation.get(
            "action",
            "",
        )
        recommendation_key = recommendation.get(
            "key",
            "unknown:key",
        )

        print(f"{index}. [{priority}] " f"{category} - {title}")
        print(f"   Key: {recommendation_key}")

        if message:
            print(f"   Why: {message}")

        if action:
            print(f"   Action: {action}")


def display_recommendation_history(
    records: list[RecommendationRecord],
) -> None:
    """Display recommendation lifecycle history."""
    print("\nRecommendation History")
    print("----------------------------------------")

    if not records:
        print("No recommendation history " "is available.")
        return

    sorted_records = sorted(
        records,
        key=lambda record: record.updated_at,
        reverse=True,
    )

    for index, record in enumerate(
        sorted_records,
        start=1,
    ):
        print(f"{index}. " f"[{record.status.name}] " f"{record.recommendation_key}")
        print(f"   Updated: " f"{record.updated_at.isoformat()}")

        if record.note:
            print(f"   Note: {record.note}")


def display_financial_snapshot(
    snapshot: dict,
) -> None:
    """Display the complete financial snapshot."""
    print("\n========================================")
    print("          Financial Snapshot")
    print("========================================")

    print(f"Total Income:          " f"${snapshot['total_income']:.2f}")
    print(f"Total Expenses:        " f"${snapshot['total_expenses']:.2f}")
    print(f"Net Cash Flow:         " f"${snapshot['net_cash_flow']:.2f}")
    print(f"Account Balance:       " f"${snapshot['total_account_balance']:.2f}")
    print(f"Goal Progress:         " f"${snapshot['total_goal_progress']:.2f}")
    print(f"Total Debt:            " f"${snapshot['total_debt']:.2f}")
    print(f"Net Worth:             " f"${snapshot['net_worth']:.2f}")
    print(
        f"Financial Health:      "
        f"{snapshot['health_score']} "
        f"({snapshot['health_status']})"
    )

    accounts = snapshot.get("accounts", [])
    goals = snapshot.get("goals", [])
    debts = snapshot.get("debts", [])
    bills = snapshot.get("bills", [])

    print("\nDomain Summary")
    print("----------------------------------------")
    print(f"Accounts:              {len(accounts)}")
    print(f"Goals:                 {len(goals)}")
    print(f"Debts:                 {len(debts)}")
    print(f"Bills:                 {len(bills)}")

    recommendations = snapshot.get(
        "recommendations",
        [],
    )

    print("\nTop Recommendations")
    print("----------------------------------------")

    if not recommendations:
        print("No recommendations are available.")
    else:
        for index, recommendation in enumerate(
            recommendations[:5],
            start=1,
        ):
            priority = recommendation.get(
                "priority",
                "UNKNOWN",
            )
            category = recommendation.get(
                "category",
                "General",
            )
            title = recommendation.get(
                "title",
                "Recommendation",
            )
            message = recommendation.get(
                "message",
                "",
            )
            action = recommendation.get(
                "action",
                "",
            )

            print(f"{index}. [{priority}] " f"{category} - {title}")

            if message:
                print(f"   Why: {message}")

            if action:
                print(f"   Action: {action}")

    print("========================================")


def display_financial_trends(
    history: list[FinancialSnapshotRecord],
) -> None:
    """Display financial changes and interpreted trends."""
    print("\n========================================")
    print("           Financial Trends")
    print("========================================")

    if not history:
        print("No financial snapshots have been recorded.")
        print("========================================")
        return

    ordered_history = sorted(
        history,
        key=lambda record: record.timestamp,
    )

    latest_snapshot = ordered_history[-1]

    formatted_timestamp = latest_snapshot.timestamp.strftime("%Y-%m-%d %H:%M")

    print(f"Snapshots Recorded:    " f"{len(ordered_history)}")
    print(f"Latest Snapshot:       " f"{formatted_timestamp}")

    trend_summary = analyze_financial_trends(ordered_history)

    if len(ordered_history) < 2:
        print("\nRecord at least two snapshots " "to calculate financial trends.")
        print(f"Overall Momentum:      " f"{trend_summary.overall_momentum.value}")
        print("========================================")
        return

    print("\nTrend Intelligence")
    print("----------------------------------------")
    print(f"Overall Momentum:      " f"{trend_summary.overall_momentum.value}")
    print(f"Net Worth Trend:       " f"{trend_summary.net_worth.direction.value}")
    print(f"Cash Flow Trend:       " f"{trend_summary.cash_flow.direction.value}")
    print(f"Income Trend:          " f"{trend_summary.income.direction.value}")
    print(f"Expense Trend:         " f"{trend_summary.expenses.direction.value}")
    print(f"Health Trend:          " f"{trend_summary.health_score.direction.value}")

    print("\nChanges")
    print("----------------------------------------")
    print(f"Net Worth Change:      " f"{_format_signed_currency(
            trend_summary.net_worth.change
        )}")
    print(f"Cash Flow Change:      " f"{_format_signed_currency(
            trend_summary.cash_flow.change
        )}")
    print(f"Income Change:         " f"{_format_signed_currency(
            trend_summary.income.change
        )}")
    print(f"Expense Change:        " f"{_format_signed_currency(
            trend_summary.expenses.change
        )}")
    print(f"Health Score Change:   " f"{_format_signed_number(
            int(trend_summary.health_score.change)
        )}")
    print("========================================")


def _display_currency_projection(
    projection: MetricProjection,
) -> None:
    """Display one currency-based forecast projection."""
    print(f"\n{projection.metric}")
    print(f"Current:               " f"${projection.current_value:,.2f}")
    print(f"Projected:             " f"${projection.projected_value:,.2f}")
    print(f"Change:                " f"{_format_signed_currency(
            projection.projected_change
        )}")


def _display_number_projection(
    projection: MetricProjection,
) -> None:
    """Display one numeric forecast projection."""
    print(f"\n{projection.metric}")
    print(f"Current:               " f"{projection.current_value:.0f}")
    print(f"Projected:             " f"{projection.projected_value:.0f}")
    print(f"Change:                " f"{_format_signed_number(
            round(projection.projected_change)
        )}")


def display_financial_forecast(
    forecast: FinancialForecast,
) -> None:
    """Display a complete financial forecast."""
    generated_at = forecast.generated_at.strftime("%Y-%m-%d %H:%M")

    print("\n========================================")
    print("          Financial Forecast")
    print("========================================")
    print(f"Forecast Horizon:      " f"{forecast.horizon_days} days")
    print(f"History Points:        " f"{forecast.history_points}")
    print(f"Generated:             " f"{generated_at}")

    if forecast.history_points < 2:
        print("\nOnly one historical snapshot is available.")
        print(
            "Projected values will remain unchanged " "until more history is recorded."
        )

    _display_currency_projection(forecast.net_worth)
    _display_currency_projection(forecast.cash_flow)
    _display_currency_projection(forecast.account_balance)
    _display_currency_projection(forecast.goal_progress)
    _display_currency_projection(forecast.total_debt)
    _display_number_projection(forecast.health_score)

    print("========================================")
    print("Forecasts are estimates based on " "historical linear trends.")


def display_scenario_management_menu() -> None:
    """Display the financial scenario menu."""
    print("\nFinancial Scenario Modeling")
    print("1. Reduce an Expense Category")
    print("2. Increase Income")
    print("3. Add Monthly Savings")
    print("4. Make an Extra Debt Payment")
    print("5. Build Combined Plan")
    print("6. Run Financial Optimizer")
    print("7. Open Planning Workspace")
    print("8. Back")


def _display_scenario_impact(
    impact: ScenarioImpact,
) -> None:
    """Display one scenario impact."""
    print(f"\n{impact.metric}")
    print(f"Current:               " f"{impact.original_value:,.2f}")
    print(f"Projected:             " f"{impact.projected_value:,.2f}")
    print(f"Change:                " f"{impact.change:+,.2f}")


def display_scenario_result(
    result: ScenarioResult,
) -> None:
    """Display a complete financial scenario result."""
    comparison_report = build_scenario_comparison_report(result)

    print("\n========================================")
    print("          Financial Scenario")
    print("========================================")
    print(f"Scenario:              {result.name}")
    print(f"Type:                  " f"{result.scenario_type.value}")

    if result.description:
        print(f"Description:           " f"{result.description}")

    print("\nAssumptions")
    print("----------------------------------------")

    if not result.assumptions:
        print("No assumptions were recorded.")
    else:
        for assumption in result.assumptions:
            print(f"{assumption.name}: " f"{assumption.value}")

            if assumption.description:
                print(f"  {assumption.description}")

    print("\nScenario Comparison")
    print("----------------------------------------")
    print(comparison_report.summary)

    print("\nMetric Comparisons")
    print("----------------------------------------")

    if not comparison_report.comparisons:
        print("No comparable financial metrics " "were found.")
    else:
        for comparison in comparison_report.comparisons:
            print(format_metric_comparison(comparison))
            print()

    print("Comparison Summary")
    print("----------------------------------------")
    print(f"Improvements:          " f"{len(comparison_report.improvements)}")
    print(f"Declines:              " f"{len(comparison_report.declines)}")
    print(f"Unchanged:             " f"{len(comparison_report.unchanged)}")

    print("\nScenario-Specific Impacts")
    print("----------------------------------------")

    if not result.impacts:
        print("No scenario-specific impacts " "were calculated.")
    else:
        for impact in result.impacts:
            _display_scenario_impact(impact)

    print("\nBenefits")
    print("----------------------------------------")

    if not result.benefits:
        print("No specific benefits were identified.")
    else:
        for benefit in result.benefits:
            print(f"- {benefit}")

    print("\nRisks")
    print("----------------------------------------")

    if not result.risks:
        print("No significant risks were identified.")
    else:
        for risk in result.risks:
            print(f"- {risk}")

    print("\nRecommendations")
    print("----------------------------------------")

    if not result.recommendations:
        print("No additional recommendations.")
    else:
        for recommendation in result.recommendations:
            print(f"- {recommendation}")

    print("========================================")


def display_combined_plan_builder_menu(
    requests: list[ScenarioRequest],
) -> None:
    """Display the combined-plan builder menu."""
    print("\nCombined Financial Plan Builder")
    print(f"Current Steps: {len(requests)}")
    print("1. Add Expense Reduction")
    print("2. Add Income Increase")
    print("3. Add Monthly Savings")
    print("4. Add Extra Debt Payment")
    print("5. Review Plan Steps")
    print("6. Remove Plan Step")
    print("7. Run Combined Plan")
    print("8. Cancel")


def display_combined_plan_steps(
    requests: list[ScenarioRequest],
) -> None:
    """Display selected combined-plan requests."""
    print("\nCombined Plan Steps")
    print("----------------------------------------")

    if not requests:
        print("No scenario steps have been added.")
        return

    for index, request in enumerate(
        requests,
        start=1,
    ):
        print(f"{index}. {request.name} " f"({request.scenario_type.value})")


def display_combined_plan_result(
    plan: ScenarioPlanResult,
) -> None:
    """Display a completed combined scenario plan."""
    print("\n========================================")
    print("        Combined Financial Plan")
    print("========================================")
    print(f"Plan:                  {plan.name}")

    if plan.description:
        print(f"Description:           " f"{plan.description}")

    print("\nSteps")
    print("----------------------------------------")

    if not plan.steps:
        print("No scenario steps were completed.")
    else:
        for step in plan.steps:
            print(f"{step.order}. " f"{step.result.name}")

    report = plan.cumulative_report

    print("\nCumulative Comparison")
    print("----------------------------------------")
    print(report.summary)

    if not report.comparisons:
        print("No comparable metrics were found.")
    else:
        for comparison in report.comparisons:
            print()
            print(format_metric_comparison(comparison))

    print("\nCumulative Summary")
    print("----------------------------------------")
    print(f"Improvements:          " f"{len(report.improvements)}")
    print(f"Declines:              " f"{len(report.declines)}")
    print(f"Unchanged:             " f"{len(report.unchanged)}")

    print("\nKey Changes")
    print("----------------------------------------")
    print(f"Net Worth Change:      " f"{_format_signed_currency(
            plan.get_metric_change(METRIC_NET_WORTH)
        )}")
    print(f"Cash Flow Change:      " f"{_format_signed_currency(
            plan.get_metric_change(METRIC_NET_CASH_FLOW)
        )}")

    debt_change = plan.get_metric_change(METRIC_TOTAL_DEBT)

    debt_reduction = max(
        -debt_change,
        0.0,
    )

    print(f"Debt Reduction:        " f"${debt_reduction:,.2f}")

    print("\nConflicts")
    print("----------------------------------------")

    if not plan.conflicts:
        print("No conflicts detected.")
    else:
        for conflict in plan.conflicts:
            print(f"- {conflict}")

    print("\nBenefits")
    print("----------------------------------------")

    if not plan.benefits:
        print("No combined benefits were identified.")
    else:
        for benefit in plan.benefits:
            print(f"- {benefit}")

    print("\nRisks")
    print("----------------------------------------")

    if not plan.risks:
        print("No significant combined risks " "were identified.")
    else:
        for risk in plan.risks:
            print(f"- {risk}")

    print("\nRecommendations")
    print("----------------------------------------")

    if not plan.recommendations:
        print("No combined recommendations " "were generated.")
    else:
        for recommendation in plan.recommendations:
            print(f"- {recommendation}")

    print("========================================")


def display_optimizer_menu() -> None:
    """Display the financial optimizer menu."""
    print("\nFinancial Plan Optimizer")
    print("1. Optimize Overall Plan")
    print("2. Maximize Net Worth")
    print("3. Improve Cash Flow")
    print("4. Reduce Debt")
    print("5. Find Lowest-Risk Option")
    print("6. Find Most Sustainable Option")
    print("7. Back")


def display_scenario_score(
    scenario_score: ScenarioScore,
) -> None:
    """Display a scenario score summary."""
    print(f"Overall Score:         " f"{scenario_score.overall_score:.2f}/100")
    print(f"Rating:                " f"{scenario_score.rating.value}")
    print(f"Risk Level:            " f"{scenario_score.risk_level.value}")
    print(f"Sustainability:        " f"{scenario_score.sustainability.value}")

    print("\nScore Components")
    print("----------------------------------------")

    for component in scenario_score.components:
        print(
            f"{component.name:<25}"
            f"{component.score:>7.2f}/100 "
            f"({component.weight * 100:.0f}%)"
        )

    print("\nOptimizer Recommendation")
    print("----------------------------------------")
    print(scenario_score.recommendation)


def display_optimizer_result(
    result: OptimizationResult,
) -> None:
    """Display a completed financial optimization result."""
    print("\n========================================")
    print("       Financial Optimization")
    print("========================================")
    print(f"Ranking Objective:     " f"{result.ranking_metric.value}")
    print(f"Candidates Generated:  " f"{result.candidate_count}")
    print(f"Successful Candidates: " f"{result.success_count}")
    print(f"Failed Candidates:     " f"{result.failure_count}")

    if not result.ranked_scenarios:
        print("\nNo viable optimization scenarios " "were generated.")

        if result.failures:
            print("\nCandidate Failures")
            print("----------------------------------------")

            for failure in result.failures:
                print(f"- {failure.candidate_name}: " f"{failure.error}")

        print("========================================")
        return

    print("\nRanked Recommendations")
    print("----------------------------------------")

    for ranked in result.ranked_scenarios:
        print(f"{ranked.rank}. " f"{ranked.scenario_name}")
        print(f"   Ranking Score: " f"{ranked.score:,.2f}")
        print(f"   Overall Score: " f"{ranked.scenario_score.overall_score:.2f}/100")
        print(f"   Rating: " f"{ranked.scenario_score.rating.value}")
        print(f"   Risk: " f"{ranked.scenario_score.risk_level.value}")
        print(f"   Sustainability: " f"{ranked.scenario_score.sustainability.value}")
        print(f"   Why: {ranked.reason}")

    best = result.best_scenario

    print("\nBest Recommended Scenario")
    print("----------------------------------------")

    if best is None:
        print("No best scenario was identified.")
    else:
        print(best.scenario_name)
        display_scenario_score(best.scenario_score)

    if result.failures:
        print("\nCandidate Failures")
        print("----------------------------------------")

        for failure in result.failures:
            print(f"- {failure.candidate_name}: " f"{failure.error}")

    print("========================================")

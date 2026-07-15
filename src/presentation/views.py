from src.financial.forecasting.models import (
    FinancialForecast,
    MetricProjection,
)
from src.financial.budgets.service import get_budgets
from src.financial.expenses.analytics import (
    get_average,
    get_category_totals,
    get_highest_expense,
    get_total,
)
from src.financial.expenses.service import get_expenses
from src.financial.history.analytics import (
    get_cash_flow_change,
    get_expense_change,
    get_health_score_change,
    get_income_change,
    get_net_worth_change,
)
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.recommendations.history import RecommendationRecord
from src.financial.reports.budget_report import build_budget_report
from src.financial.shared.categories import ExpenseCategory
from src.financial.history.trends import analyze_financial_trends
from src.financial.scenarios.models import (
    ScenarioImpact,
    ScenarioResult,
)


def _format_signed_currency(value: float) -> str:
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
    print("14. Exit")


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
    print(
        f"Net Worth Change:      "
        f"{_format_signed_currency(
            trend_summary.net_worth.change
        )}"
    )
    print(
        f"Cash Flow Change:      "
        f"{_format_signed_currency(
            trend_summary.cash_flow.change
        )}"
    )
    print(
        f"Income Change:         "
        f"{_format_signed_currency(
            trend_summary.income.change
        )}"
    )
    print(
        f"Expense Change:        "
        f"{_format_signed_currency(
            trend_summary.expenses.change
        )}"
    )
    print(
        f"Health Score Change:   "
        f"{_format_signed_number(
            int(trend_summary.health_score.change)
        )}"
    )
    print("========================================")


def _display_currency_projection(
    projection: MetricProjection,
) -> None:
    """Display one currency-based forecast projection."""
    print(f"\n{projection.metric}")
    print(f"Current:               " f"${projection.current_value:,.2f}")
    print(f"Projected:             " f"${projection.projected_value:,.2f}")
    print(
        f"Change:                "
        f"{_format_signed_currency(
            projection.projected_change
        )}"
    )


def _display_number_projection(
    projection: MetricProjection,
) -> None:
    """Display one numeric forecast projection."""
    print(f"\n{projection.metric}")
    print(f"Current:               " f"{projection.current_value:.0f}")
    print(f"Projected:             " f"{projection.projected_value:.0f}")
    print(
        f"Change:                "
        f"{_format_signed_number(
            round(projection.projected_change)
        )}"
    )


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
    print("5. Back")


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
    print("\n========================================")
    print("          Financial Scenario")
    print("========================================")
    print(f"Scenario:              {result.name}")
    print(f"Type:                  " f"{result.scenario_type.value}")

    if result.description:
        print(f"Description:           {result.description}")

    print("\nAssumptions")
    print("----------------------------------------")

    if not result.assumptions:
        print("No assumptions were recorded.")
    else:
        for assumption in result.assumptions:
            print(f"{assumption.name}: " f"{assumption.value}")

    print("\nFinancial Impacts")
    print("----------------------------------------")

    if not result.impacts:
        print("No financial impacts were calculated.")
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

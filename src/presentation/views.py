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
    category_totals = get_category_totals(
        expenses
    )
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
        print(
            f"Largest Expense:    "
            f"{highest.name} - "
            f"${highest.amount:.2f}"
        )

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
    print("12. Exit")


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
    totals = get_category_totals(
        get_expenses()
    )

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
    print(
        f"Remaining: "
        f"${summary['remaining']:.2f}"
    )
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
        print(
            "\nNo budgets have been created yet."
        )
        return

    print("\nCurrent Budgets")
    print("----------------")

    for budget in budgets:
        print(
            f"{budget.category.value:<20}"
            f"${budget.limit:>8.2f}"
        )


def display_recommendations(
    recommendations: list[dict],
) -> None:
    """Display active serialized recommendations."""
    print("\nActive Recommendations")
    print("----------------------------------------")

    if not recommendations:
        print(
            "No active recommendations "
            "are available."
        )
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

        print(
            f"{index}. [{priority}] "
            f"{category} - {title}"
        )
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
        print(
            "No recommendation history "
            "is available."
        )
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
        print(
            f"{index}. "
            f"[{record.status.name}] "
            f"{record.recommendation_key}"
        )
        print(
            f"   Updated: "
            f"{record.updated_at.isoformat()}"
        )

        if record.note:
            print(f"   Note: {record.note}")


def display_financial_snapshot(
    snapshot: dict,
) -> None:
    """Display the complete financial snapshot."""
    print("\n========================================")
    print("          Financial Snapshot")
    print("========================================")

    print(
        f"Total Income:          "
        f"${snapshot['total_income']:.2f}"
    )
    print(
        f"Total Expenses:        "
        f"${snapshot['total_expenses']:.2f}"
    )
    print(
        f"Net Cash Flow:         "
        f"${snapshot['net_cash_flow']:.2f}"
    )
    print(
        f"Account Balance:       "
        f"${snapshot['total_account_balance']:.2f}"
    )
    print(
        f"Goal Progress:         "
        f"${snapshot['total_goal_progress']:.2f}"
    )
    print(
        f"Total Debt:            "
        f"${snapshot['total_debt']:.2f}"
    )
    print(
        f"Net Worth:             "
        f"${snapshot['net_worth']:.2f}"
    )
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

            print(
                f"{index}. [{priority}] "
                f"{category} - {title}"
            )

            if message:
                print(f"   Why: {message}")

            if action:
                print(f"   Action: {action}")

    print("========================================")


def display_financial_trends(
    history: list[FinancialSnapshotRecord],
) -> None:
    """Display financial changes across saved snapshots."""
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

    print(
        f"Snapshots Recorded:    "
        f"{len(ordered_history)}"
    )
    print(
        f"Latest Snapshot:       "
        f"{latest_snapshot.timestamp.isoformat()}"
    )

    if len(ordered_history) < 2:
        print(
            "\nRecord at least two snapshots "
            "to calculate financial trends."
        )
        print("========================================")
        return

    net_worth_change = get_net_worth_change(
        ordered_history
    )
    cash_flow_change = get_cash_flow_change(
        ordered_history
    )
    income_change = get_income_change(
        ordered_history
    )
    expense_change = get_expense_change(
        ordered_history
    )
    health_score_change = get_health_score_change(
        ordered_history
    )

    print("\nChanges")
    print("----------------------------------------")
    print(
        f"Net Worth Change:      "
        f"{_format_signed_currency(net_worth_change)}"
    )
    print(
        f"Cash Flow Change:      "
        f"{_format_signed_currency(cash_flow_change)}"
    )
    print(
        f"Income Change:         "
        f"{_format_signed_currency(income_change)}"
    )
    print(
        f"Expense Change:        "
        f"{_format_signed_currency(expense_change)}"
    )
    print(
        f"Health Score Change:   "
        f"{_format_signed_number(health_score_change)}"
    )
    print("========================================")
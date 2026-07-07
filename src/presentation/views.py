from src.financial.expenses.analytics import (
    get_average,
    get_category_totals,
    get_highest_expense,
    get_total,
)
from src.financial.budgets.analytics import get_budget_summary
from src.financial.budgets.service import get_budgets
from src.financial.shared.categories import ExpenseCategory
from src.financial.expenses.service import get_expenses
from src.financial.reports.budget_report import build_budget_report

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

    print("\n==============================")
    print("        Financial Core")
    print("==============================")
    print(f"Expenses:           {len(expenses)}")
    print(f"Total Spending:     ${total:.2f}")
    print(f"Average Expense:    ${average:.2f}")

    if highest is not None:
        print(f"Largest Expense:    {highest.name} - ${highest.amount:.2f}")

    if category_totals:
        top_category = max(category_totals, key=category_totals.get)
        print(
            f"Top Category:       {top_category} - "
            f"${category_totals[top_category]:.2f}"
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
    print("9. Exit")


def display_categories() -> None:
    """Display available expense categories."""
    print("\nCategories:")
    for index, category in enumerate(ExpenseCategory, start=1):
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
            f"ID {expense.id}: {expense.name} | "
            f"{expense.category.value} | "
            f"${expense.amount:.2f}"
        )


def display_category_totals() -> None:
    """Display spending totals grouped by category."""
    totals = get_category_totals(get_expenses())

    if not totals:
        print("No expenses recorded yet.")
        return

    print("\nCategory Totals:")
    for category, total in totals.items():
        print(f"{category}: ${total:.2f}")


def display_budget_summary(summary: dict) -> None:
    """Display a budget summary report."""
    print("\nBudget Summary:")
    print(f"Category:  {summary['category']}")
    print(f"Limit:     ${summary['limit']:.2f}")
    print(f"Spent:     ${summary['spent']:.2f}")
    print(f"Remaining: ${summary['remaining']:.2f}")
    print(f"Status:    {summary['status']}")


def display_saved_budget_summaries() -> None:
    """Display summaries for all saved budgets."""
    budgets = get_budgets()
    expenses = get_expenses()

    if not budgets:
        print("No budgets configured yet.")
        return

    report = build_budget_report(budgets, expenses)

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
        print(
            f"{budget.category.value:<20}"
            f"${budget.limit:>8.2f}"
        )
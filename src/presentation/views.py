from src.financial.categories import ExpenseCategory
from src.financial.expense_tracker import get_expenses
from src.financial.analytics import (
    get_average,
    get_category_totals,
    get_highest_expense,
    get_total,
)
from src.financial.budget_service import get_budgets
from src.financial.budget_analytics import get_budget_summary

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
        print(f"Top Category:       {top_category} - ${category_totals[top_category]:.2f}")

    print("==============================")

def show_menu() -> None:
    """Display the main menu."""
    print("\nFinancial Core")
    print("1. Add expense")
    print("2. View expenses")
    print("3. View total spending")
    print("4. Delete expense")
    print("5. Update expense")
    print("6. View category totals")
    print("7. View budget summary")
    print("8. View saved budget summaries")
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

    print("\nSaved Budget Summaries:")
    for budget in budgets:
        summary = get_budget_summary(budget, expenses)
        print(
            f"{summary['category']}: "
            f"Limit ${summary['limit']:.2f} | "
            f"Spent ${summary['spent']:.2f} | "
            f"Remaining ${summary['remaining']:.2f} | "
            f"{summary['status']}"
        )
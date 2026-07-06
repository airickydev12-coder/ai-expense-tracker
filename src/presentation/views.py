from src.financial.analytics import get_category_totals
from src.financial.categories import ExpenseCategory
from src.financial.expense_tracker import get_expenses


def show_menu() -> None:
    """Display the main menu."""
    print("\nFinancial Core")
    print("1. Add expense")
    print("2. View expenses")
    print("3. View total spending")
    print("4. Delete expense")
    print("5. Update expense")
    print("6. View category totals")
    print("7. Exit")


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
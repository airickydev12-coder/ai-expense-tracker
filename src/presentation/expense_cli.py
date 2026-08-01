from decimal import Decimal, InvalidOperation

from src.financial.expenses.service import (
    add_expense,
    delete_expense,
    update_expense,
)
from src.presentation.input_handlers import select_category
from src.presentation.views import display_expenses


def add_expense_flow() -> None:
    """Collect input and create an expense."""
    name = input("Expense name: ").strip()
    category = select_category()

    if category is None:
        return

    amount_text = input("Amount: ").strip()

    try:
        amount = Decimal(amount_text)
    except ValueError, InvalidOperation:
        print("Invalid amount. Please enter a number.")
        return

    if amount < 0:
        print("Amount cannot be negative.")
        return

    add_expense(
        name,
        category,
        amount,
    )

    print("Expense added successfully!")


def delete_expense_flow() -> None:
    """Collect input and delete an expense."""
    display_expenses()

    expense_id_text = input("Enter the expense ID to delete: ").strip()

    try:
        expense_id = int(expense_id_text)
    except ValueError, InvalidOperation:
        print("Invalid input. Please enter a number.")
        return

    deleted_expense = delete_expense(expense_id)

    if deleted_expense is None:
        print("Expense not found.")
        return

    print(f"Deleted expense: {deleted_expense.name}")


def update_expense_flow() -> None:
    """Collect input and update an expense."""
    display_expenses()

    expense_id_text = input("Enter the expense ID to update: ").strip()

    try:
        expense_id = int(expense_id_text)
    except ValueError, InvalidOperation:
        print("Invalid input. Please enter a number.")
        return

    new_name = input("New name (press Enter to keep unchanged): ")

    category_input = input("Change category? (y/n): ").strip().lower()

    category = None

    if category_input == "y":
        category = select_category()

        if category is None:
            return

    new_amount_text = input("New amount (press Enter to keep unchanged): ").strip()

    name = new_name.strip() or None
    amount = None

    if new_amount_text:
        try:
            amount = Decimal(new_amount_text)
        except ValueError, InvalidOperation:
            print("Invalid amount. Please enter a number.")
            return

        if amount < 0:
            print("Amount cannot be negative.")
            return

    updated_expense = update_expense(
        expense_id=expense_id,
        name=name,
        category=category,
        amount=amount,
    )

    if updated_expense is None:
        print("Expense not found.")
        return

    print(f"Updated expense: {updated_expense.name}")

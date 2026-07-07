from src.financial.analytics import get_total
from src.presentation.input_handlers import select_category
from src.financial.expense_tracker import (
    add_expense,
    delete_expense,
    get_expenses,
    load_expenses,
    update_expense,
)
from src.presentation.views import (
    display_budget_summary,
    display_categories,
    display_category_totals,
    display_dashboard,
    display_expenses,
    show_menu,
)

from src.financial.budget_analytics import get_budget_summary
from src.financial.budget_models import Budget

def run_cli() -> None:
    """Run the command-line interface."""
    load_expenses()
    display_dashboard()

    while True:
        show_menu()
        choice = input("Choose an option: ")

        if choice == "1":
            name = input("Expense name: ")
            category = select_category()

            if category is None:
                continue

            amount_text = input("Amount: ")

            try:
                amount = float(amount_text)
            except ValueError:
                print("Invalid amount. Please enter a number.")
                continue

            add_expense(name, category, amount)
            print("Expense added successfully!")

        elif choice == "2":
            display_expenses()

        elif choice == "3":
            total = get_total(get_expenses())
            print(f"Total spending: ${total:.2f}")

        elif choice == "4":
            display_expenses()

            expense_id_text = input("Enter the expense ID to delete: ")

            try:
                expense_id = int(expense_id_text)
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            deleted_expense = delete_expense(expense_id)

            if deleted_expense is None:
                print("Expense not found.")
            else:
                print(f"Deleted expense: {deleted_expense.name}")

        elif choice == "5":
            display_expenses()

            expense_id_text = input("Enter the expense ID to update: ")

            try:
                expense_id = int(expense_id_text)
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            new_name = input("New name (press Enter to keep unchanged): ")

            print("Choose a new category, or press Enter to keep unchanged.")
            category_input = input("Change category? (y/n): ").lower().strip()

            category = None
            if category_input == "y":
                category = select_category()
                if category is None:
                    continue

            new_amount_text = input("New amount (press Enter to keep unchanged): ")

            name = new_name.strip() if new_name.strip() else None
            amount = None

            if new_amount_text.strip():
                try:
                    amount = float(new_amount_text)
                except ValueError:
                    print("Invalid amount. Please enter a number.")
                    continue

                if amount < 0:
                    print("Amount cannot be negative.")
                    continue

            updated_expense = update_expense(
                expense_id=expense_id,
                name=name,
                category=category,
                amount=amount,
            )

            if updated_expense is None:
                print("Expense not found.")
            else:
                print(f"Updated expense: {updated_expense.name}")

        elif choice == "6":
            display_category_totals()

        
        elif choice == "7":
            category = select_category()

            if category is None:
                continue

            limit_text = input("Budget limit: ")

            try:
                limit = float(limit_text)
            except ValueError:
                print("Invalid budget limit. Please enter a number.")
                continue

            budget = Budget(category=category, limit=limit)
            summary = get_budget_summary(budget, get_expenses())

            display_budget_summary(summary)

        elif choice == "8":
            print("Goodbye!")
            break

        elif choice == "8":
            print("Exit")
            break

        else:
            print("Invalid option. Please choose 1, 2, 3, 4, 5, 6, 7, or 8.")
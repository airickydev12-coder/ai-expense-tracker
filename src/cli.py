from src.financial.expense_tracker import (
    add_expense,
    get_expenses,
    calculate_total,
    load_expenses,
    delete_expense,
    update_expense,
)


def show_menu() -> None:
    """Display the main menu."""
    print("\nFinancial Core")
    print("1. Add expense")
    print("2. View expenses")
    print("3. View total spending")
    print("4. Delete expense")
    print("5. Update expense")
    print("6. Exit")

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
            f"{expense.category} | "
            f"${expense.amount:.2f}"
        )


def run_cli() -> None:
    """Run the command-line interface."""
    load_expenses()

    while True:
        show_menu()
        choice = input("Choose an option: ")

        if choice == "1":
            name = input("Expense name: ")
            category = input("Category: ")
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
            calculate_total()

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
            new_category = input("New category (press Enter to keep unchanged): ")
            new_amount_text = input("New amount (press Enter to keep unchanged): ")

            name = new_name.strip() if new_name.strip() else None
            category = new_category.strip() if new_category.strip() else None
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
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please choose 1, 2, 3, 4, 5, or 6.")